'''Read a CSV file and build a plain-text summary report.'''

import csv
import statistics
from pathlib import Path


def read_rows(path: str | Path) -> list[dict[str, str]]:
    '''Return the rows of the CSV file at ``path`` as a list of dictionaries.'''
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))
    

def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
    
    
def build_report(rows: list[dict[str, str]]) -> str:
    '''Summarise ``rows`` as text.
    
    The report has the row count, then the total, average, minimum and maximum
    of every column whose non-empty values are all numbers.
    '''
    
    lines = [f'Rows: {len(rows)}']
    
    for column in rows[0] if rows else []:
        values = [(row.get(column) or '').strip() for row in rows]
        values = [value for value in values if value]
        numbers = [_to_float(value) for value in values]
        if values and None not in numbers:
            lines.append(
                f'{column}: total={sum(numbers):.2f} '
                f'average={statistics.mean(numbers):.2f} '
                f'min={min(numbers):.2f} max={max(numbers):.2f}'
            )
    return '\n'.join(lines)
    
    
    

