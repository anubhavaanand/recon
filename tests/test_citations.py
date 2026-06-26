import pytest

from core.citations import (
    CitationGraph,
    CitationNode,
    _clean_patent_id,
    _mock_backward,
    _mock_forward,
    fetch_citations,
)
from tui.widgets.citation_tree import CitationTree, _format_node


class TestCleanPatentId:
    def test_strips_language_suffix(self):
        assert _clean_patent_id("US12046712B2(en)") == "US12046712B2"

    def test_strips_asterisk(self):
        assert _clean_patent_id("KR102272556B1(en)*") == "KR102272556B1"

    def test_strips_dagger(self):
        assert _clean_patent_id("EP3238290B1(en)†") == "EP3238290B1"

    def test_plain_id_unchanged(self):
        assert _clean_patent_id("US10000001B2") == "US10000001B2"

    def test_empty_string(self):
        assert _clean_patent_id("") == ""


class TestCitationNode:
    def test_node_creation(self):
        node = CitationNode(id="US123", title="Test", assignee="Acme", date="2020-01-01")
        assert node.id == "US123"
        assert node.title == "Test"
        assert node.assignee == "Acme"
        assert node.date == "2020-01-01"

    def test_node_defaults(self):
        node = CitationNode(id="US123", title="", assignee="", date="")
        assert node.id == "US123"


class TestCitationGraph:
    def test_graph_creation(self):
        bwd = [CitationNode(id="B1", title="Back", assignee="X", date="2020-01-01")]
        fwd = [CitationNode(id="F1", title="Fwd", assignee="Y", date="2021-01-01")]
        graph = CitationGraph(patent_id="P1", assignee="Owner", backward=bwd, forward=fwd)
        assert graph.patent_id == "P1"
        assert len(graph.backward) == 1
        assert len(graph.forward) == 1

    def test_graph_default_empty_lists(self):
        graph = CitationGraph(patent_id="P1", assignee="Owner")
        assert graph.backward == []
        assert graph.forward == []


class TestMockData:
    def test_mock_backward_returns_five_nodes(self):
        nodes = _mock_backward("US123")
        assert len(nodes) == 5
        for n in nodes:
            assert isinstance(n, CitationNode)
            assert n.id

    def test_mock_forward_returns_three_nodes(self):
        nodes = _mock_forward("US123")
        assert len(nodes) == 3
        for n in nodes:
            assert isinstance(n, CitationNode)
            assert n.id


class TestFormatNode:
    def test_format_node_with_all_fields(self):
        node = CitationNode(id="US123B2", title="Battery Tech", assignee="Tesla", date="2020-01-01")
        result = _format_node(node)
        assert "US123B2" in result
        assert "Battery Tech" in result
        assert "Tesla" in result
        assert "2020-01-01" in result

    def test_format_node_with_missing_title(self):
        node = CitationNode(id="US123B2", title="[?]", assignee="[?]", date="")
        result = _format_node(node)
        assert "US123B2" in result
        assert "[?]" in result

    def test_format_node_short_title_truncated(self):
        long_title = "A" * 100
        node = CitationNode(id="US1", title=long_title, assignee="X", date="2020-01-01")
        result = _format_node(node)
        assert len(result) < 200  # sanity check - not enormous


class TestBuildTree:
    def test_tree_contains_root_patent(self):
        graph = CitationGraph(patent_id="US123", assignee="Acme")
        tree = CitationTree._build_tree(graph)
        assert "US123" in tree
        assert "Acme" in tree

    def test_tree_contains_forward_section(self):
        graph = CitationGraph(patent_id="P1", assignee="X")
        tree = CitationTree._build_tree(graph)
        assert "Cited by" in tree

    def test_tree_contains_backward_section(self):
        graph = CitationGraph(
            patent_id="P1", assignee="X",
            backward=[CitationNode(id="B1", title="T", assignee="A", date="2020-01-01")],
        )
        tree = CitationTree._build_tree(graph)
        assert "Cites" in tree
        assert "B1" in tree

    def test_tree_shows_none_when_empty(self):
        graph = CitationGraph(patent_id="P1", assignee="X")
        tree = CitationTree._build_tree(graph)
        assert "None found" in tree

    def test_tree_shows_forward_and_backward(self):
        graph = CitationGraph(
            patent_id="P1", assignee="X",
            forward=[CitationNode(id="F1", title="Fwd", assignee="Y", date="2021-01-01")],
            backward=[CitationNode(id="B1", title="Bwd", assignee="Z", date="2020-01-01")],
        )
        tree = CitationTree._build_tree(graph)
        assert "F1" in tree
        assert "B1" in tree
        assert "Fwd" in tree
        assert "Bwd" in tree


@pytest.mark.asyncio
async def test_fetch_citations_returns_graph(monkeypatch):
    """fetch_citations should return a CitationGraph."""
    graph = await fetch_citations("US123", "Test Corp")
    assert isinstance(graph, CitationGraph)
    assert graph.patent_id == "US123"
    assert graph.assignee == "Test Corp"


@pytest.mark.asyncio
async def test_fetch_citations_falls_back_to_mock(monkeypatch):
    """When scraper returns empty, mock data should be used."""
    async def mock_backward(*args, **kwargs):
        return []

    async def mock_forward(*args, **kwargs):
        return []

    monkeypatch.setattr("core.citations._fetch_backward_citations", mock_backward)
    monkeypatch.setattr("core.citations._fetch_forward_citations", mock_forward)

    graph = await fetch_citations("US123", "Test Corp")
    assert len(graph.backward) == 5  # mock
    assert len(graph.forward) == 3  # mock
