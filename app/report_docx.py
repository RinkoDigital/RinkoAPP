import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from app.schemas import DriverPayReport


def _money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def _rate_label(rate_cents: int | None) -> str:
    return f"{_money(rate_cents)} / delivered package" if rate_cents is not None else "Varies by client"


def _add_heading(document: Document, text: str) -> None:
    heading = document.add_paragraph()
    run = heading.add_run(text)
    run.bold = True
    run.font.size = Pt(12)


def _set_cell_text(cell, text: str, bold: bool = False) -> None:
    cell.text = ""
    run = cell.paragraphs[0].add_run(text)
    run.bold = bold


def _key_value_table(document: Document, rows: list[tuple[str, str]]) -> None:
    table = document.add_table(rows=len(rows), cols=2)
    table.style = "Table Grid"
    for i, (key, value) in enumerate(rows):
        _set_cell_text(table.rows[i].cells[0], key, bold=True)
        _set_cell_text(table.rows[i].cells[1], value)


def render_driver_pay_report_docx(report: DriverPayReport) -> bytes:
    document = Document()

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(report.company_name.upper())
    run.bold = True
    run.font.size = Pt(16)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("LAST-MILE DELIVERY — DRIVER PERFORMANCE & PAY REPORT")
    run.bold = True
    run.font.size = Pt(11)

    _key_value_table(
        document,
        [
            ("Driver:", report.driver_name),
            ("Reporting Period:", f"{report.period_start} to {report.period_end}"),
            ("Pay Rate:", _rate_label(report.overall_summary.rate_cents)),
            ("Operation:", "Last-Mile Delivery"),
            ("Report Status:", "Final"),
            ("Prepared By:", report.company_name),
        ],
    )

    document.add_paragraph()
    _add_heading(document, "DELIVERY DETAIL")
    headers = [
        "Week",
        "Date",
        "Client",
        "Assigned",
        "Exceptions / Returns",
        "Payable Delivered",
        "Rate",
        "Amount",
        "Payment Status",
    ]
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, header in zip(table.rows[0].cells, headers):
        _set_cell_text(cell, header, bold=True)
    for row in report.delivery_detail:
        cells = table.add_row().cells
        _set_cell_text(cells[0], f"Week {row.week_number}")
        _set_cell_text(cells[1], row.batch_date.isoformat())
        _set_cell_text(cells[2], row.client_name)
        _set_cell_text(cells[3], str(row.assigned_count))
        _set_cell_text(cells[4], str(row.exceptions_count))
        _set_cell_text(cells[5], str(row.payable_count))
        _set_cell_text(cells[6], _money(row.rate_cents))
        _set_cell_text(cells[7], _money(row.amount_due_cents))
        _set_cell_text(cells[8], row.payment_status.value.upper())

    document.add_paragraph()
    _add_heading(document, "CLIENT SUMMARY")
    headers = [
        "Client",
        "Assigned",
        "Exceptions / Returns",
        "Payable Delivered",
        "Completion Rate",
        "Compensation",
    ]
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, header in zip(table.rows[0].cells, headers):
        _set_cell_text(cell, header, bold=True)
    for row in report.client_summary:
        cells = table.add_row().cells
        _set_cell_text(cells[0], row.client_name)
        _set_cell_text(cells[1], str(row.assigned_count))
        _set_cell_text(cells[2], str(row.exceptions_count))
        _set_cell_text(cells[3], str(row.payable_count))
        _set_cell_text(cells[4], f"{row.completion_rate:.2f}%")
        _set_cell_text(cells[5], _money(row.compensation_cents))

    document.add_paragraph()
    _add_heading(document, "OVERALL SUMMARY")
    summary = report.overall_summary
    _key_value_table(
        document,
        [
            ("Packages Assigned", str(summary.assigned_count)),
            ("Exceptions / Returns", str(summary.exceptions_count)),
            ("Payable Deliveries", str(summary.payable_count)),
            ("Overall Delivery Completion Rate", f"{summary.completion_rate:.2f}%"),
            ("Rate per Delivered Package", _rate_label(summary.rate_cents)),
            ("TOTAL DRIVER COMPENSATION", _money(summary.total_compensation_cents)),
        ],
    )

    document.add_paragraph()
    table = document.add_table(rows=2, cols=4)
    table.style = "Table Grid"
    _set_cell_text(table.rows[0].cells[0], "Driver Signature:", bold=True)
    _set_cell_text(table.rows[0].cells[2], "Date:", bold=True)
    _set_cell_text(table.rows[1].cells[0], "Operations Manager Approval:", bold=True)
    _set_cell_text(table.rows[1].cells[2], "Payment Date:", bold=True)

    document.add_paragraph()
    _add_heading(document, "PAYMENT RECONCILIATION")
    reconciliation = report.payment_reconciliation
    _key_value_table(
        document,
        [
            ("Total Earned", _money(reconciliation.total_earned_cents)),
            ("Already Paid", _money(reconciliation.already_paid_cents)),
            ("TOTAL OUTSTANDING BALANCE", _money(reconciliation.outstanding_balance_cents)),
        ],
    )

    if reconciliation.paid_items:
        document.add_paragraph()
        note = document.add_paragraph()
        note.add_run("Payment notes:").bold = True
        for item in reconciliation.paid_items:
            document.add_paragraph(
                f"{item.batch_date.isoformat()} — {item.client_name} — "
                f"{item.payable_count} payable deliveries × {_money(item.rate_cents)} = "
                f"{_money(item.amount_cents)} — PAID. Included in earned totals and "
                f"deducted from the outstanding balance.",
                style="List Bullet",
            )

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
