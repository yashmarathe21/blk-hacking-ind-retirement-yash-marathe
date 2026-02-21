# BlackRock India Retirement Savings API

A FastAPI-based retirement savings calculator that helps users analyze their investment strategies for retirement planning in India. The API processes expense transactions, applies period-based transformations, and calculates returns for both NPS (National Pension Scheme) and NIFTY 50 index investments.

## Features

- **Transaction Processing**: Enrich transactions with ceiling and remnant calculations
- **Validation**: Check for negative amounts and duplicate transactions
- **Period-Based Transformations**:
  - **Q Periods (Override)**: Replace remnants with fixed amounts for specific date ranges
  - **P Periods (Bonus)**: Add extra amounts to remnants during promotional periods
  - **K Periods (Evaluation)**: Group transactions for investment calculation and analysis
- **Investment Returns**: Calculate compound interest returns adjusted for inflation
- **Tax Benefits**: Compute Indian tax benefits for NPS investments
- **Performance Monitoring**: Track system metrics (memory, threads, response time)

## API Endpoints

### 1. Parse Transactions

**POST** `/blackrock/challenge/v1/transactions:parse`

Enriches transactions with ceiling (rounded to nearest 100) and remnant (savings potential).

### 2. Validate Transactions

**POST** `/blackrock/challenge/v1/transactions:validator`

Validates transactions for negative amounts and duplicates.

### 3. Filter Transactions

**POST** `/blackrock/challenge/v1/transactions:filter`

Applies Q, P, and K period transformations to transactions.

### 4. NPS Returns

**POST** `/blackrock/challenge/v1/returns:nps`

Calculates NPS investment returns (7.11% rate) with tax benefits.

### 5. NIFTY 50 Returns

**POST** `/blackrock/challenge/v1/returns:index`

Calculates NIFTY 50 index returns (14.49% rate) without tax benefits.

### 6. Performance Metrics

**GET** `/blackrock/challenge/v1/performance`

Returns system performance metrics.

## Installation

### Prerequisites

- Python 3.14
- Docker (optional)

### Local Setup

1. Clone the repository:

```bash
git clone https://github.com/yashmarathe21/blk-hacking-ind-retirement-yash-marathe
cd blk-hacking-ind-retirement
```

2. Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
uvicorn app.main:app --reload --port 5477
```

The API will be available at `http://localhost:5477`

### Docker Setup

1. Build the Docker image:

```bash
docker build -t blk-hacking-ind-yash-marathe .
```

2. Run the container:

```bash
docker run -p 5477:5477 blk-hacking-ind-yash-marathe
```

The API will be available at `http://localhost:5477`
