"""
Simulator persistence service.

Writes the generated world to PostgreSQL.
Handles the insertion order required by the circular FK between
customers.subscription_id and subscriptions.customer_id.

ARCHITECTURE:
  SimulatorOutcome rows are written here and are ONLY readable by the
  evaluation harness (Phase 4) via this module — never by agent code.
"""
import logging
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.customer import Customer
from app.db.models.subscription import Subscription
from app.db.models.payment import Payment
from app.db.models.event import Event
from app.db.models.simulation_run import SimulationRun, SimulatorOutcome
from app.simulator.world import WorldInternal
from app.simulator.outcomes import ACTION_TYPES

logger = logging.getLogger(__name__)


def persist_world(db: Session, world: WorldInternal) -> SimulationRun:
    """
    Persist a generated world to PostgreSQL.

    Returns the SimulationRun record for the caller to track the run.
    Writes SimulatorOutcome rows — these are simulator-internal and
    must not be exposed to observable APIs.
    """
    t_start = time.time()

    # 1. Create simulation run record
    run = SimulationRun(
        seed=world.seed,
        cohort_size=world.cohort_size,
        simulator_version=world.simulator_version,
        status="generating",
    )
    db.add(run)
    db.flush()  # get run.id

    logger.info(
        "Persisting world",
        extra={
            "kp_simulation_run_id": run.id,
            "kp_seed": world.seed,
            "kp_cohort_size": world.cohort_size,
        },
    )

    # 2. Insert customers (subscription_id = NULL initially)
    customer_orm_map: dict[int, Customer] = {}
    for rec in world.records:
        c = Customer(
            name=rec.name,
            segment=rec.segment,
            ltv=rec.ltv,
            subscription_id=None,  # set after subscriptions are created
        )
        db.add(c)
        customer_orm_map[rec.customer_id] = c

    db.flush()  # assign customer IDs

    # Build mapping: generator customer_id → real DB customer ID
    # (generator uses 1..N; DB uses auto-incremented IDs)
    gen_id_to_db_id: dict[int, int] = {}
    for gen_id, c_orm in customer_orm_map.items():
        gen_id_to_db_id[gen_id] = c_orm.id

    # 3. Insert subscriptions
    sub_orm_map: dict[int, Subscription] = {}
    for rec in world.records:
        db_customer_id = gen_id_to_db_id[rec.customer_id]
        sub_data = rec.subscription
        s = Subscription(
            customer_id=db_customer_id,
            plan=sub_data["plan"],
            amount=sub_data["amount"],
            currency=sub_data["currency"],
            renewal_at=sub_data["renewal_at"],
            status=sub_data["status"],
        )
        db.add(s)
        sub_orm_map[rec.customer_id] = s

    db.flush()  # assign subscription IDs

    # 4. Update customers.subscription_id
    for gen_id, s_orm in sub_orm_map.items():
        customer_orm_map[gen_id].subscription_id = s_orm.id

    db.flush()

    # 5. Insert payments
    payment_count = 0
    for rec in world.records:
        db_customer_id = gen_id_to_db_id[rec.customer_id]
        db_sub_id = sub_orm_map[rec.customer_id].id
        for p_data in rec.payments:
            p = Payment(
                customer_id=db_customer_id,
                subscription_id=db_sub_id,
                amount=p_data["amount"],
                status=p_data["status"],
                failure_code=p_data["failure_code"],
                payment_method=p_data["payment_method"],
                created_at=p_data["created_at"],
            )
            db.add(p)
            payment_count += 1

    db.flush()

    # 6. Insert observable events
    event_count = 0
    for rec in world.records:
        db_customer_id = gen_id_to_db_id[rec.customer_id]
        for e_data in rec.events:
            e = Event(
                customer_id=db_customer_id,
                event_type=e_data["event_type"],
                timestamp=e_data["timestamp"],
                payload=e_data["payload"],
            )
            db.add(e)
            event_count += 1

    db.flush()

    # 7. Insert simulator outcomes — HIDDEN from observable APIs
    outcome_count = 0
    for rec in world.records:
        db_customer_id = gen_id_to_db_id[rec.customer_id]
        for action_type in ACTION_TYPES:
            action_outcome = rec.potential_outcomes.for_action(action_type)
            o = SimulatorOutcome(
                simulation_run_id=run.id,
                customer_id=db_customer_id,
                action_type=action_type,
                p_payment=round(action_outcome.p_payment, 4),
                p_churn=round(action_outcome.p_churn, 4),
            )
            db.add(o)
            outcome_count += 1

    db.flush()

    # 8. Mark run completed
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()

    duration = time.time() - t_start
    logger.info(
        "World persisted",
        extra={
            "kp_simulation_run_id": run.id,
            "kp_customer_count": len(world.records),
            "kp_event_count": event_count,
            "kp_payment_count": payment_count,
            "kp_outcome_count": outcome_count,
            "kp_duration_seconds": round(duration, 2),
        },
    )

    return run
