# Data Flow Diagram

## Data Flow

RetailIQ follows a linear but reusable data flow from source files to executive outputs.

```mermaid
flowchart TD
    R1[Olist Raw CSVs in data/raw] --> R2[Preprocessing
load, clean, validate]
    R2 --> R3[Processed Tables in data/processed]
    R3 --> R4[Feature Engineering
order, customer, product, seller features]
    R4 --> R5[Feature Marts]
    R5 --> R6[KPI Engine]
    R5 --> R7[SQL Queries]
    R5 --> R8[EDA Notebook]
    R6 --> R9[Executive KPI DataFrames]
    R7 --> R10[Business Analysis Outputs]
    R8 --> R11[Insights and Visual Exploration]
    R9 --> R12[Power BI Blueprint]
    R10 --> R12
    R11 --> R12
```

## Input Tables

- Orders
- Order items
- Order payments
- Order reviews
- Customers
- Sellers
- Products
- Category translation
- Geolocation

## Transformation Stages

### Stage 1: Preprocessing
- Read all raw inputs
- Normalize schema
- Remove duplicates
- Fill gaps in critical fields
- Parse timestamps

### Stage 2: Feature Engineering
- Build order-level and item-level facts
- Build customer and seller dimensions
- Add monthly, weekly, and geographic attributes

### Stage 3: KPI Computation
- Total revenue
- Total orders
- Average order value
- Profit margin when cost data exists
- Repeat customer rate
- Customer retention
- Revenue by state and category

### Stage 4: Reporting Outputs
- EDA notebook
- SQL business queries
- Power BI executive dashboard blueprint
- Leadership memo

## Output Principles

- Each output layer is reusable.
- Each transformation is traceable.
- Business logic is centralized to avoid metric drift.