"""Export sessions as normalized JSON."""

from __future__ import annotations

import json
from dataclasses import asdict

from ..models import Session
from ..normalize import derive_title


def export_json(session: Session) -> str:
    data = {
        "title": derive_title(session),
        "messages": [asdict(m) for m in session.messages],
        "metadata": session.metadata,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
