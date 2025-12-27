import csv
import json
import os

from utils.performance_monitor import PerformanceMonitor


def test_export_history_csv(tmp_path):
    """Test exporting history to CSV format."""
    monitor = PerformanceMonitor(history_size=10)

    # Add some dummy data
    for _ in range(5):
        monitor.record_frame(0.016)
        monitor.record_detection(0.005)

    filepath = tmp_path / "test_stats.csv"
    success = monitor.export_history(str(filepath), format="csv")

    assert success
    assert os.path.exists(filepath)

    with open(filepath, encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Check header structure
        assert "SAI Color Tracker V3 Performance Export" in rows[0][0]
        assert "Date:" in rows[1][0]
        assert "Average FPS:" in rows[2][0]

        # Check data header
        header_row_index = 4
        assert rows[header_row_index] == ["Frame Index", "FPS", "Frame Time (ms)", "Detection Time (ms)"]

        # Check data rows (should be 5 rows of data)
        data_start_index = header_row_index + 1
        assert len(rows) - data_start_index == 5

        # Check values in first data row
        first_data = rows[data_start_index]
        assert first_data[0] == "0"
        assert float(first_data[2]) == 16.0
        assert float(first_data[3]) == 5.0

def test_export_history_json(tmp_path):
    """Test exporting history to JSON format."""
    monitor = PerformanceMonitor(history_size=10)

    # Add some dummy data
    for _ in range(5):
        monitor.record_frame(0.016)

    filepath = tmp_path / "test_stats.json"
    success = monitor.export_history(str(filepath), format="json")

    assert success
    assert os.path.exists(filepath)

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

        assert "timestamp" in data
        assert "stats" in data
        assert "history" in data
        assert len(data["history"]["frame_times"]) == 5
        assert data["history"]["frame_times"][0] == 16.0
