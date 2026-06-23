from textual.widgets import Static
from textual.reactive import reactive


class AlertBanner(Static):
    alerts = reactive(list)

    def watch_alerts(self, alerts: list):
        if not alerts:
            self.styles.display = "none"
            return

        self.styles.display = "block"
        lines = []
        for alert in alerts:
            severity = alert.get("severity", "unknown").upper()
            metric = alert.get("metric", "unknown")
            value = alert.get("value", 0)
            threshold = alert.get("threshold", 0)
            rb = alert.get("runbook", "")

            if severity == "CRITICAL":
                icon = "!"
            elif severity == "HIGH":
                icon = "!"
            else:
                icon = "i"

            source = alert.get("source", "")
            src_label = f" [{source}]" if source else ""
            lines.append(
                f"[{icon}] [{severity}] {metric}{src_label}: "
                f"{value:.2f} (threshold: {threshold}) | Runbook: {rb}"
            )

        self.update("\n".join(lines))

    CSS = """
    AlertBanner {
        display: none;
        height: auto;
        background: $surface-darken-2;
        color: $text;
        padding: 1;
        border-bottom: solid $warning;
    }
    """
