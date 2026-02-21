from datetime import datetime
from math import ceil
from typing import List, Optional
import logging

from app.models import PeriodK, PeriodP, PeriodQ, TransactionBase, TransactionEnriched

logger = logging.getLogger(__name__)


def _format_datetime(dt: datetime) -> str:
    """Format datetime to YYYY-MM-DD HH:MM:SS format."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _parse_datetime(date_str: str) -> datetime:
    """Parse YYYY-MM-DD HH:MM:SS format to datetime."""
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


def _apply_q_periods(
    transaction_date: datetime, base_remnant: float, override_periods: List[PeriodQ]
) -> float:
    """Apply q period rules: use period with latest start date if multiple match."""
    best_q_period = None
    for period in override_periods:
        if period.start <= transaction_date <= period.end:
            if best_q_period is None or period.start > best_q_period.start:
                best_q_period = period

    if best_q_period:
        logger.debug(
            f"Q period applied for {_format_datetime(transaction_date)}: "
            f"remnant changed from {base_remnant} to {best_q_period.fixed}"
        )
        return best_q_period.fixed
    return base_remnant


def _apply_p_periods(
    transaction_date: datetime, remnant: float, bonus_periods: List[PeriodP]
) -> float:
    """Apply p period rules: add extra for all matching periods."""
    initial_remnant = remnant
    for period in bonus_periods:
        if period.start <= transaction_date <= period.end:
            remnant += period.extra
            logger.debug(
                f"P period applied for {_format_datetime(transaction_date)}: "
                f"added {period.extra}, remnant now {remnant}"
            )
    if remnant != initial_remnant:
        logger.debug(
            f"Total P period adjustment for {_format_datetime(transaction_date)}: "
            f"{initial_remnant} -> {remnant}"
        )
    return remnant


def _check_k_periods(
    transaction_date: datetime, evaluation_periods: List[PeriodK]
) -> bool:
    """Check if transaction falls within any k evaluation period.

    k Period Rules (Evaluation Grouping):
    - For each k period: sum up remnant of all transactions whose dates fall in range (inclusive)
    - A transaction can belong to multiple k periods
    - Each k period calculates its sum independently
    - Any k range is within a calendar year (not spanning multiple years)

    Returns True if transaction falls in any k period, False otherwise.
    """
    for period in evaluation_periods:
        if period.start <= transaction_date <= period.end:
            return True
    return False


def get_performance_metrics() -> dict:
    """Get current system performance metrics."""
    import psutil
    import threading

    now = datetime.now()
    timestamp = _format_datetime(now) + f".{now.microsecond // 1000:03d}"

    return {
        "time": timestamp,
        "memory": f"{psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB",
        "threads": threading.active_count(),
    }


def _check_validation_errors(amount: float, transaction_key: tuple, seen: set) -> list:
    """Check for negative amounts and duplicates. Returns list of errors."""
    errors = []
    if amount < 0:
        errors.append("Negative amounts are not allowed")
    if transaction_key in seen:
        errors.append("Duplicate transaction")
    return errors


def _validate_transaction(
    transaction: TransactionBase, seen: set
) -> tuple[dict, tuple, list]:
    """Check for negative amounts and duplicates. Returns (dict, key, errors)."""
    transaction_dict = transaction.model_dump()
    transaction_key = (transaction.date, transaction.amount)
    errors = _check_validation_errors(transaction.amount, transaction_key, seen)

    return transaction_dict, transaction_key, "; ".join(errors)


def enrich_transactions(transactions: list[TransactionBase]) -> list[dict]:
    """Enrich transactions with ceiling and remnant calculations."""
    logger.info(f"Enriching {len(transactions)} transactions")
    result = []
    for t in transactions:
        ceiling = ceil(t.amount / 100) * 100
        remnant = ceiling - t.amount
        logger.debug(
            f"Transaction {_format_datetime(t.date)}: amount={t.amount}, "
            f"ceiling={ceiling}, remnant={remnant}"
        )
        result.append(
            {
                "date": _format_datetime(t.date),
                "amount": t.amount,
                "ceiling": ceiling,
                "remnant": remnant,
            }
        )
    logger.info(f"Enriched {len(result)} transactions successfully")
    return result


def validate_transactions(transactions: list[TransactionEnriched]) -> dict:
    """Validate transactions for negative amounts and duplicates."""
    valid = []
    invalid = []
    seen = set()

    for transaction in transactions:
        transaction_dict, transaction_key, errors = _validate_transaction(
            transaction, seen
        )

        if errors:
            transaction_dict["message"] = errors
            invalid.append(transaction_dict)
        else:
            seen.add(transaction_key)
            valid.append(transaction_dict)

    return {"valid": valid, "invalid": invalid}


def filter_transactions_by_periods(
    transactions: list[TransactionBase],
    override_periods: Optional[List[PeriodQ]],
    bonus_periods: Optional[List[PeriodP]],
    evaluation_periods: Optional[List[PeriodK]],
) -> dict:
    """Filter and transform transactions based on periods."""
    enriched = enrich_transactions(transactions)

    valid = []
    invalid = []
    seen = set()

    override_periods = override_periods or []
    bonus_periods = bonus_periods or []
    evaluation_periods = evaluation_periods or []

    for enriched_dict in enriched:
        transaction_key = (enriched_dict["date"], enriched_dict["amount"])
        errors = _check_validation_errors(
            enriched_dict["amount"], transaction_key, seen
        )

        if errors:
            invalid.append(
                {
                    "date": enriched_dict["date"],
                    "amount": enriched_dict["amount"],
                    "message": "; ".join(errors),
                }
            )
            continue

        seen.add(transaction_key)

        transaction_date = _parse_datetime(enriched_dict["date"])

        remnant = _apply_q_periods(
            transaction_date, enriched_dict["remnant"], override_periods
        )
        remnant = _apply_p_periods(transaction_date, remnant, bonus_periods)
        in_k_period = _check_k_periods(transaction_date, evaluation_periods)

        enriched_dict["remnant"] = remnant
        enriched_dict["inKPeriod"] = in_k_period

        if remnant > 0:
            valid.append(enriched_dict)

    return {"valid": valid, "invalid": invalid}


def calculate_tax(income: float) -> float:
    """Calculate tax based on simplified Indian tax slabs."""
    if income <= 700000:
        return 0.0
    elif income <= 1000000:
        return (income - 700000) * 0.10
    elif income <= 1200000:
        return 300000 * 0.10 + (income - 1000000) * 0.15
    elif income <= 1500000:
        return 300000 * 0.10 + 200000 * 0.15 + (income - 1200000) * 0.20
    else:
        return 300000 * 0.10 + 200000 * 0.15 + 300000 * 0.20 + (income - 1500000) * 0.30


def get_returns(amount, years, rate, inflation):
    """Calculate investment returns with compound interest and inflation adjustment.

    Note: Inflation is expected in percentage format (e.g., 5.5 for 5.5%) and will be converted to decimal.
    """
    n = 1

    nominal_final = amount * ((1 + rate / n) ** (n * years))
    real_final = nominal_final / ((1 + inflation) ** years)

    logger.debug(f"get_returns result: nominal={nominal_final}, real={real_final}")

    return real_final


def _validate_enriched_transactions(enriched: list[dict]) -> list[dict]:
    """Validate enriched transactions for negative amounts and duplicates.

    Returns only valid transactions.
    """
    seen = set()
    valid_enriched = []

    for enriched_dict in enriched:
        transaction_key = (enriched_dict["date"], enriched_dict["amount"])
        errors = _check_validation_errors(
            enriched_dict["amount"], transaction_key, seen
        )

        if errors:
            logger.warning(
                f"Skipping invalid transaction {enriched_dict['date']}: {'; '.join(errors)}"
            )
            continue

        seen.add(transaction_key)
        valid_enriched.append(enriched_dict)

    logger.info(
        f"Valid transactions after validation: {len(valid_enriched)} out of {len(enriched)}"
    )
    return valid_enriched


def _process_transactions_with_periods(
    enriched: list[dict],
    override_periods: List[PeriodQ],
    bonus_periods: List[PeriodP],
) -> tuple[list[dict], float, float]:
    """Process enriched transactions applying q and p periods."""
    total_amount = 0.0
    total_ceiling = 0.0
    processed_transactions = []

    for enriched_dict in enriched:
        transaction_date = _parse_datetime(enriched_dict["date"])

        remnant = _apply_q_periods(
            transaction_date, enriched_dict["remnant"], override_periods
        )
        remnant = _apply_p_periods(transaction_date, remnant, bonus_periods)

        total_amount += enriched_dict["amount"]
        total_ceiling += enriched_dict["ceiling"]

        if remnant > 0:
            processed_transactions.append(
                {
                    "date": transaction_date,
                    "amount": enriched_dict["amount"],
                    "ceiling": enriched_dict["ceiling"],
                    "remnant": remnant,
                }
            )
            logger.debug(
                f"Processed transaction {_format_datetime(transaction_date)}: "
                f"amount={enriched_dict['amount']}, final_remnant={remnant}"
            )
        else:
            logger.debug(
                f"Skipped transaction {_format_datetime(transaction_date)}: remnant={remnant} <= 0"
            )

    logger.info(
        f"Total transactions processed: {len(processed_transactions)}, total_amount={total_amount}, total_ceiling={total_ceiling}"
    )

    return processed_transactions, total_amount, total_ceiling


def _calculate_k_period_savings(
    k_period: PeriodK,
    processed_transactions: list[dict],
    age: int,
    rate: float,
    inflation: float,
    annual_income: float,
    should_calculate_tax: bool,
) -> dict:
    """Calculate savings, profits, and tax benefit for a single k period."""
    logger.info(
        f"Processing K period: {_format_datetime(k_period.start)} to "
        f"{_format_datetime(k_period.end)}"
    )

    period_investment = 0.0
    for trans in processed_transactions:
        if k_period.start <= trans["date"] <= k_period.end:
            period_investment += trans["remnant"]
            logger.debug(
                f"Included: {_format_datetime(trans['date'])}, amount={trans['amount']}, remnant={trans['remnant']}"
            )

    logger.info(f"K period total investment: {period_investment}")

    years = 60 - age if age < 60 else 5
    real_value = get_returns(period_investment, years, rate, inflation)
    profit = real_value - period_investment

    logger.info(
        f"Returns calculation: investment={period_investment}, years={years}, "
        f"rate={rate}, inflation={inflation}, real_value={real_value}, profit={profit}"
    )

    tax_benefit = 0.0
    if should_calculate_tax and period_investment > 0:
        nps_deduction = min(period_investment, 0.10 * annual_income, 200000)
        tax_without_deduction = calculate_tax(annual_income)
        tax_with_deduction = calculate_tax(annual_income - nps_deduction)
        tax_benefit = tax_without_deduction - tax_with_deduction

        logger.info(
            f"Tax benefit calculation: nps_deduction={nps_deduction}, "
            f"tax_without={tax_without_deduction}, tax_with={tax_with_deduction}, "
            f"benefit={tax_benefit}"
        )

    return {
        "start": _format_datetime(k_period.start),
        "end": _format_datetime(k_period.end),
        "amount": round(period_investment, 2),
        "profits": round(profit, 2),
        "taxBenefit": round(tax_benefit, 2),
    }


def calculate_returns(
    transactions: list[TransactionBase],
    override_periods: List[PeriodQ],
    bonus_periods: List[PeriodP],
    evaluation_periods: List[PeriodK],
    age: int,
    wage: float,
    inflation: float,
    rate: float,
    should_calculate_tax: bool,
) -> dict:
    """Calculate returns on investments with period-based transformations."""
    logger.info(
        f"Calculating returns: age={age}, wage={wage}, inflation={inflation}, "
        f"rate={rate}, transactions={len(transactions)}, "
        f"q_periods={len(override_periods)}, p_periods={len(bonus_periods)}, "
        f"k_periods={len(evaluation_periods)}, should_calculate_tax={should_calculate_tax}"
    )

    enriched = enrich_transactions(transactions)
    valid_enriched = _validate_enriched_transactions(enriched)

    processed_transactions, total_amount, total_ceiling = (
        _process_transactions_with_periods(
            valid_enriched, override_periods, bonus_periods
        )
    )

    annual_income = wage * 12
    inflation = inflation / 100
    logger.info(f"Annual income: {annual_income}, Inflation: {inflation}")

    savings_by_dates = []
    for k_period in evaluation_periods:
        k_savings = _calculate_k_period_savings(
            k_period,
            processed_transactions,
            age,
            rate,
            inflation,
            annual_income,
            should_calculate_tax,
        )
        savings_by_dates.append(k_savings)

    return {
        "totalTransactionAmount": round(total_amount, 2),
        "totalCeiling": round(total_ceiling, 2),
        "savingsByDates": savings_by_dates,
    }


def calculate_nps_returns(
    transactions: list[TransactionBase],
    override_periods: List[PeriodQ],
    bonus_periods: List[PeriodP],
    evaluation_periods: List[PeriodK],
    age: int,
    wage: float,
    inflation: float,
) -> dict:
    """Calculate NPS returns with 7.11% rate and tax benefits."""
    return calculate_returns(
        transactions,
        override_periods,
        bonus_periods,
        evaluation_periods,
        age,
        wage,
        inflation,
        rate=0.0711,
        should_calculate_tax=True,
    )


def calculate_index_returns(
    transactions: list[TransactionBase],
    override_periods: List[PeriodQ],
    bonus_periods: List[PeriodP],
    evaluation_periods: List[PeriodK],
    age: int,
    wage: float,
    inflation: float,
) -> dict:
    """Calculate NIFTY 50 index returns with 14.49% rate and no tax benefits."""
    return calculate_returns(
        transactions,
        override_periods,
        bonus_periods,
        evaluation_periods,
        age,
        wage,
        inflation,
        rate=0.1449,
        should_calculate_tax=False,
    )
