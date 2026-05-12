import pytest
from core.search import sort_and_merge_results
from core.models import PatentRecord

def test_descending_sort_never_drops():
    records = [
        PatentRecord(id="1", title="A", assignee="X", dates={"filed": "2020-01-01"}, abstract="", claims=[], image_urls=[], status="active", family_id="F1"),
        PatentRecord(id="2", title="B", assignee="Y", dates={"filed": "2021-01-01"}, abstract="", claims=[], image_urls=[], status="active", family_id="F2"),
        PatentRecord(id="3", title="C", assignee="Z", dates={"filed": "2019-01-01"}, abstract="", claims=[], image_urls=[], status="active", family_id="F3"),
    ]
    
    sorted_records = sort_and_merge_results(records)
    
    # Must never drop entries
    assert len(sorted_records) == 3
    
    # Must be descending by filed date (2021, 2020, 2019)
    assert sorted_records[0].id == "2"
    assert sorted_records[1].id == "1"
    assert sorted_records[2].id == "3"
