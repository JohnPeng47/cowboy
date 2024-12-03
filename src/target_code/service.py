from src.ast.models import NodeModel
from src.target_code.models import TargetCode, TargetCodeModel
from src.test_modules.models import TestModuleModel
from src.coverage.models import CoverageModel

from sqlalchemy.orm import Session

def delete_target_code(db_session: Session, tm_id: int):
    """Delete all target code for a test module."""

    deleted = (
        db_session.query(TargetCodeModel)
        .filter(TargetCodeModel.test_module_id == tm_id)
        .delete()
    )

    db_session.commit()

    return deleted
