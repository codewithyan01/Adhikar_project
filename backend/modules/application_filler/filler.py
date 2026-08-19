"""Application Auto-Filler Module (Module B).

Transforms matched scheme application templates and collected user profile slots
into a verified, downloadable application dossier with document checklists.
"""

from typing import Dict, Any, Optional
from backend.core.document_generator import DocumentGenerator


class ApplicationFiller:
    """Module B: Auto-Populates government scheme application forms."""

    def __init__(self):
        self.doc_gen = DocumentGenerator()

    def create_application_dossier(
        self,
        scheme_name: str,
        application_process: str,
        user_profile: Dict[str, Any],
        source_url: str = ""
    ) -> Dict[str, Any]:
        """Creates structured preview and instructions."""
        return self.doc_gen.generate_application_preview(
            scheme_name=scheme_name,
            template_text=application_process,
            user_profile=user_profile,
            source_url=source_url
        )

    def export_pdf(
        self,
        scheme_name: str,
        application_process: str,
        user_profile: Dict[str, Any],
        source_url: str = ""
    ) -> bytes:
        """Exports official PDF document stream."""
        return self.doc_gen.generate_application_pdf(
            scheme_name=scheme_name,
            template_text=application_process,
            user_profile=user_profile,
            source_url=source_url
        )


default_application_filler = ApplicationFiller()

def generate_scheme_application(
    scheme_name: str,
    application_process: str,
    user_profile: Dict[str, Any],
    source_url: str = ""
) -> Dict[str, Any]:
    return default_application_filler.create_application_dossier(
        scheme_name, application_process, user_profile, source_url
    )
