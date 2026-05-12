from textual.widgets import Static
from core.models import PatentRecord
from core.scoring import calculate_signal_score

class InfoTab(Static):
    def update_record(self, record: PatentRecord | None):
        if not record:
            self.update("No patent selected.")
            return

        date_filed = record.dates.get("filed", "[?]")
        
        # Calculate intelligence score
        score = calculate_signal_score(record.cross_references)
        
        signals_text = ""
        if record.cross_references:
            signals_text = "\n### Intelligence Signals\n"
            for ref in record.cross_references:
                confidence = ref.metadata.get('confidence', 100.0)
                signals_text += f"- **{ref.source}**: {ref.url} (Match: {confidence:.1f}%)\n"
        else:
            signals_text = "\n### Intelligence Signals\nNo external signals found."

        content = f"""
# {record.title}
**ID**: {record.id} | **Assignee**: {record.assignee} | **Filed**: {date_filed} | **Status**: {record.status}
**Signal Score**: {score}/100

## Abstract
{record.abstract}
{signals_text}
"""
        self.update(content)
