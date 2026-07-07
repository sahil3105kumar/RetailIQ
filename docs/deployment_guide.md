# Deployment Guide

## Purpose

This guide explains how to set up and run the RetailIQ project in a reproducible way for local analysis or portfolio demonstration.

## Prerequisites

- Python 3.12 or compatible
- Virtual environment support
- Access to the Olist CSV files
- Power BI Desktop for dashboard implementation

## Local Setup

1. Create and activate the project virtual environment.
2. Install dependencies from `requirements.txt`.
3. Download the Olist dataset and place the CSV files in `data/raw`.
4. Run `python main.py --project-root /home/sahil/RetailIQ --overwrite`.
5. Confirm the cleaned and feature outputs are written to `data/processed`.

## Runtime Outputs

- Cleaned source tables
- Feature marts
- KPI DataFrames
- EDA notebook outputs
- SQL business query results

## Recommended Execution Order

1. Preprocessing
2. Feature engineering
3. KPI engine
4. SQL analytics
5. Notebook analysis
6. Power BI dashboard build

## Validation Checklist

- Raw files are present
- Required Python packages are installed
- Pipeline completes without errors
- Output row counts are sensible
- KPI numbers align across Python and SQL layers

## Delivery Notes

For a portfolio presentation, use the processed tables and executive memo to explain how the project moves from raw data to management decisions.