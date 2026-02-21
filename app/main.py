from fastapi import FastAPI
from app.models import (
    ReturnsRequest,
    TransactionBase,
    ValidatorRequest,
    FilterRequest,
)
from app.services import (
    enrich_transactions,
    validate_transactions,
    filter_transactions_by_periods,
    get_performance_metrics,
    calculate_nps_returns,
    calculate_index_returns,
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="BlackRock Savings API")


@app.post("/blackrock/challenge/v1/transactions:parse")
async def parse_transactions(transactions: list[TransactionBase]):
    return enrich_transactions(transactions)


@app.post("/blackrock/challenge/v1/transactions:validator")
async def validate_endpoint(request: ValidatorRequest):
    return validate_transactions(request.transactions)


@app.post("/blackrock/challenge/v1/transactions:filter")
async def filter_endpoint(request: FilterRequest):
    return filter_transactions_by_periods(
        request.transactions, request.q, request.p, request.k
    )


@app.post("/blackrock/challenge/v1/returns:nps")
async def returns_nps(req: ReturnsRequest):
    return calculate_nps_returns(
        req.transactions, req.q, req.p, req.k, req.age, req.wage, req.inflation
    )


@app.post("/blackrock/challenge/v1/returns:index")
async def returns_index(req: ReturnsRequest):
    return calculate_index_returns(
        req.transactions, req.q, req.p, req.k, req.age, req.wage, req.inflation
    )


@app.get("/blackrock/challenge/v1/performance")
async def performance():
    return get_performance_metrics()
