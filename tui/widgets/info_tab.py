from textual.widgets import Static
from rich.markup import escape
from core.models import PatentRecord
from core.scoring import calculate_signal_score

class InfoTab(Static):
    def update_record(self, record: PatentRecord | None):
        try:
            if not record:
                self.update("No patent selected.")
                return

            # Escape all external data to prevent Rich markup injection
            title     = escape(record.title)
            rec_id    = escape(record.id)
            assignee  = escape(record.assignee)
            status    = escape(record.status)
            abstract  = escape(record.abstract)
            date_filed = escape(record.dates.get("filed", "[?]"))
            
            # Calculate intelligence score
            score = calculate_signal_score(record.cross_references)
            
            signals_text = ""
            if record.cross_references:
                signals_text = "\n### Intelligence Signals\n"
                for ref in record.cross_references:
                    confidence = ref.metadata.get('confidence', 100.0)
                    signals_text += f"- {escape(ref.source)}: {escape(ref.url)} (Match: {confidence:.1f}%)\n"
            else:
                signals_text = "\n### Intelligence Signals\nNo external signals found."

            content = (
                f"# {title}\n"
                f"ID: {rec_id} | Assignee: {assignee} | Filed: {date_filed} | Status: {status}\n"
                f"Signal Score: {score}/100\n\n"
                f"## Abstract\n{abstract}\n"
                f"{signals_text}"
            )
            self.update(content)
        except Exception as e:
            self.update(f"ERR: Info rendering failed: {str(e)}")
