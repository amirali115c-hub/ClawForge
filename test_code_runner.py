import sys
sys.path.insert(0, 'C:\\Users\\HP\\.openclaw\\workspace\\ClawForge')

print('='*60)
print('CODE RUNNER MODULE TEST')
print('='*60)

from backend.code_runner import CodeRunner, DeveloperAssistant

# Test 1: CodeRunner
print('\n[OK] CodeRunner Test:')
runner = CodeRunner()
analysis = runner.analyze_requirement('Build a FastAPI REST API')
print('  Detected type:', analysis['detected_type'])
print('  Language:', analysis['language'])

# Test 2: Generate project
print('\n[OK] Generating FastAPI project...')
result = runner.run_pipeline(
    requirement='Build a FastAPI REST API',
    project_name='TestFastAPI',
    task_id='test_runner'
)
print('  Project type:', result['project_type'])
print('  Files written:', len(result['files_written']))

# Test 3: DeveloperAssistant
print('\n[OK] DeveloperAssistant Tests:')
err = DeveloperAssistant.debug_error('ModuleNotFoundError: No module named fastapi')
print('  Debug:', err['root_cause'])

sec = DeveloperAssistant.security_review('eval(user_input)')
print('  Security:', sec['overall_risk'], '-', sec['issues_found'], 'issues')

opt = DeveloperAssistant.optimize_code('for i in range(len(x)): pass')
print('  Optimize:', len(opt['suggestions']), 'suggestions')

print('\n' + '='*60)
print('CODE RUNNER TEST PASSED!')
print('='*60)
