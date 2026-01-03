import pytest

from core.api.timetable.ttable_parser import day_weeks, day_to_index, raw_values2db_ids_handler


class _FakeConn:
    async def discipline_ids(self):
        return [{'id': 10, 'title': 'Math'}]

    async def teacher_ids(self):
        return [{'id': 5, 'fio': 'Teach A'}]

    async def group_ids(self):
        return [{'id': 7, 'name': 'GROUP1'}]


@pytest.mark.asyncio
async def test_raw_values2db_ids_handler_transforms_to_ids():
    day_name = next(iter(day_weeks.keys()))
    std_ttable = {
        "GROUP1": {
            day_name: {
                1: {
                    "discipline": "Math",
                    "auditory": "101",
                    "teachers": ["Teach A"],
                }
            }
        }
    }
    result = await raw_values2db_ids_handler(std_ttable, sched_ver_id=99, conn_obj=_FakeConn())

    assert result == [
        (99, 7, 10, 1, "101", 5, day_to_index(day_name))
    ]


def test_day_to_index_unknown():
    with pytest.raises(ValueError):
        day_to_index("unknown-day")
