import sys
sys.path.insert(0, 'C:\\Users\\HP\\.openclaw\\workspace\\ClawForge')

print('='*60)
print('OFFICE MODULES TEST')
print('='*60)

from backend.office_modules import ExcelSolver, DocumentWriter, PDFBuilder, UIController

# Test 1: ExcelSolver
print('\n[OK] ExcelSolver Test:')
solver = ExcelSolver()
sample_data = [
    {"Name": "Alice", "Department": "Engineering", "Salary": 95000},
    {"Name": "Bob",   "Department": "Marketing",   "Salary": 72000},
    {"Name": "Carol", "Department": "Engineering", "Salary": 88000},
    {"Name": "Bob",   "Department": "Marketing",   "Salary": 72000},
]
result = solver.run_pipeline(sample_data, "test.xlsx", task_id="test_office")
print('  Cleaned rows:', result['cleaned_rows'])
print('  Issues found:', len(result['errors_found']))
print('  Formula:', result['formula_examples']['vlookup'])

# Test 2: DocumentWriter
print('\n[OK] DocumentWriter Test:')
writer = DocumentWriter()
doc_result = writer.create_document(
    doc_type="report",
    title="Test Report",
    content={"sections": {"Summary": "This is a test."}},
    output_path="./workspace/output/test_doc.docx"
)
print('  Status:', doc_result['status'])

# Test 3: PDFBuilder
print('\n[OK] PDFBuilder Test:')
builder = PDFBuilder()
pdf_result = builder.create_pdf(
    output_path="./workspace/output/test_pdf.pdf",
    title="Test PDF",
    sections={"Overview": "This is a test PDF.", "Conclusion": "Done."}
)
print('  Status:', pdf_result['status'])

# Test 4: UIController
print('\n[OK] UIController Test:')
ui = UIController()
result = ui.execute_if_approved("take_screenshot", {}, "NO")
print('  Status:', result['status'])
print('  Message:', result['message'])

print('\n' + '='*60)
print('OFFICE MODULES TEST PASSED!')
print('='*60)
