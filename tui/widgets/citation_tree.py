"""ASCII tree widget for citation graph display.

Renders a CitationGraph as a navigable ASCII tree (like the Linux
`tree` command), supporting ↑/↓ scroll within a Textual Static.
"""

from __future__ import annotations

from rich.markup import escape
from textual.widgets import Static

from core.citations import CitationGraph, CitationNode


class CitationTree(Static):
    """A static widget that renders the citation graph as an ASCII tree.

    The widget renders the tree inline. Navigation is handled by the
    parent screen via scroll_up/scroll_down actions.
    """

    def render_graph(self, graph: CitationGraph) -> None:
        """Build and display the ASCII tree from a CitationGraph."""
        self.update(self._build_tree(graph))

    @staticmethod
    def _build_tree(graph: CitationGraph) -> str:
        """Build an ASCII tree string from the graph."""
        patent_id = escape(graph.patent_id)
        assignee = escape(graph.assignee) if graph.assignee else "[?]"

        lines: list[str] = [
            "# Citation Graph",
            f"{patent_id} ({assignee})",
            "│",
        ]

        backward = graph.backward or []
        forward = graph.forward or []

        # ── Forward (cited by) ──
        lines.append("├── Cited by (Forward Citations)")
        if not forward:
            lines.append("│   └── None found")
        else:
            for i, c in enumerate(forward):
                pfx = "│   └──" if i == len(forward) - 1 and not backward else "│   ├──"
                lines.append(f"{pfx} {_format_node(c)}")

        # ── Backward (cites) ──
        if backward:
            lines.append("│")
            lines.append("└── Cites (Backward Citations)")
            for i, c in enumerate(backward):
                pfx = "    └──" if i == len(backward) - 1 else "    ├──"
                lines.append(f"{pfx} {_format_node(c)}")

        return "\n".join(lines)

    def action_scroll_down(self) -> None:
        self.scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        self.scroll_up(animate=False)


def _format_node(node: CitationNode) -> str:
    """Format a single citation node for display."""
    pid = escape(node.id)
    title = escape(node.title[:60]) if node.title and node.title != "[?]" else "[?]"
    assignee = escape(node.assignee[:30]) if node.assignee and node.assignee != "[?]" else "[?]"
    date = node.date if node.date and node.date != "[?]" else ""
    date_str = f" [{date}]" if date else ""
    return f"{pid} — \"{title}\" — {assignee}{date_str}"
