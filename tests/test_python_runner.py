from src.runner.local.python import update_coverage_omits
import os

UPDATED_FILE = """[run]
relative_files = True
omit = 
            */tests/*
            *_test.py
            .env/*
            build/*
            dist/*
            test_*
            tests/*
            venv/*
"""


def test_update_coverage_omits():
    # Create a sample .coveragerc file
    sample_content = """[run]
relative_files = True"""
    
    # with open('sample.coveragerc', 'w') as f:
    #     f.write(sample_content)
    
    # Update the file
    updated_coveragerc = update_coverage_omits('sample.coveragerc')
    print(updated_coveragerc)
    assert updated_coveragerc == UPDATED_FILE

    os.remove('sample.coveragerc')
    