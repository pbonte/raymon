#%%
import pytest
import json
import pendulum
import uuid
from raymon import Trace, RaymonAPI, RaymonAPILogger, RaymonFileLogger
from raymon import types as rt
from raymon.tests.conftest import PROJECT_NAME


class Dummyreponse:

    ok = True


tags = [{"name": "my-tag", "value": "my_value", "type": "label", "group": "mygroup"}]


def test_textfile(tmp_path, monkeypatch, secret_file):

    fpath = tmp_path
    logger = RaymonFileLogger(path=fpath, project_id=PROJECT_NAME, reset_file=True)
    ray = Trace(logger=logger)
    ray.info("This is a test")
    ray.log(ref="a-test", data=rt.Native({"a": "b"}))
    ray.tag(tags=tags)

    # load log file
    with open(logger.fname, "r") as f:
        lines = f.readlines()

    # First line --info
    """
    {"type": "info", "jcr": {"timestamp": "2021-01-29T08:33:51.428387+00:00", "trace_id": "3cc9dec5-e9e5-48b4-8c5c-ba2b48460c92", "ref": null, "data": "This is a test", "project_id": "testing"}}
    """
    line = json.loads(lines[0])
    assert line["type"] == "info"
    jcr = line["jcr"]
    # No error should be raised when parsing timestamp str
    pendulum.parse(jcr["timestamp"])
    uuid.UUID(jcr["trace_id"], version=4)
    assert jcr["data"] == "This is a test"
    assert jcr["ref"] is None
    assert jcr["project_id"] == PROJECT_NAME

    # 2nd line --data
    """
    {"type": "info", "jcr": {"timestamp": "2021-01-29T08:33:51.428387+00:00", "trace_id": "3cc9dec5-e9e5-48b4-8c5c-ba2b48460c92", "ref": null, "data": "This is a test", "project_id": "testing"}}
    """
    line = json.loads(lines[1])
    assert line["type"] == "data"
    jcr = line["jcr"]
    # No error should be raised when parsing timestamp str
    pendulum.parse(jcr["timestamp"])
    uuid.UUID(jcr["trace_id"], version=4)
    assert jcr["data"]["params"]["data"]["a"] == "b"
    assert jcr["ref"] == "a-test"
    assert jcr["project_id"] == PROJECT_NAME

    # 3rd line --tags
    """
    {"type": "tags", "jcr": {"timestamp": "2021-01-29T08:33:51.473413+00:00", "trace_id": "3cc9dec5-e9e5-48b4-8c5c-ba2b48460c92", "ref": null, "data": [{"name": "my-tag", "value": "my_value", "type": "label", "group": "mygroup"}], "project_id": "testing"}}
    """
    line = json.loads(lines[2])
    assert line["type"] == "tags"
    jcr = line["jcr"]
    # No error should be raised when parsing timestamp str
    pendulum.parse(jcr["timestamp"])
    uuid.UUID(jcr["trace_id"], version=4)
    for tag_orig, tag_log in zip(tags, jcr["data"]):
        assert tag_orig["name"] == tag_log["name"]
        assert tag_orig["value"] == tag_log["value"]
        assert tag_orig["type"] == tag_log["type"]
        assert tag_orig["group"] == tag_log["group"]

    assert jcr["ref"] is None
    assert jcr["project_id"] == PROJECT_NAME


def test_2_textloggers(tmp_path):

    fpath = tmp_path  # Path(".")
    logger = RaymonFileLogger(path=fpath, project_id=PROJECT_NAME, reset_file=True)
    ray = Trace(logger=logger)
    ray.info("This is a test")
    ray.log(ref="a-test", data=rt.Native({"a": "b"}))
    ray.tag(tags=tags)

    # load log file
    with open(logger.fname, "r") as f:
        lines = f.readlines()
        assert len(lines) == 3

    logger2 = RaymonFileLogger(path=fpath, project_id=PROJECT_NAME, reset_file=True)
    ray = Trace(logger=logger2)
    ray.info("This is a test")
    ray.log(ref="a-test", data=rt.Native({"a": "b"}))
    ray.tag(tags=tags)
    ray.info("This is a test too")

    assert logger.fname != logger2.fname
    # load log file
    with open(logger2.fname, "r") as f:
        lines = f.readlines()
        assert len(lines) == 4


def test_api_logger_info(monkeypatch, secret_file):
    def dummylogin(self):
        pass

    def test_info_post(self, route, json):
        assert route == f"projects/{PROJECT_NAME}/ingest"
        jcr = json
        pendulum.parse(jcr["timestamp"])
        uuid.UUID(jcr["trace_id"], version=4)
        assert jcr["data"] == "This is a test"
        assert jcr["ref"] is None
        assert jcr["project_id"] == PROJECT_NAME
        return Dummyreponse()

    monkeypatch.setattr(RaymonAPI, "login", dummylogin)
    monkeypatch.setattr(RaymonAPI, "post", test_info_post)
    apilogger = RaymonAPILogger(url="willnotbeused", project_id=PROJECT_NAME, auth_path=secret_file)
    ray = Trace(logger=apilogger)
    ray.info("This is a test")


def test_api_logger_data(monkeypatch, secret_file):
    def dummylogin(self):
        pass

    def test_data_post(self, route, json):
        assert route == f"projects/{PROJECT_NAME}/ingest" ""
        jcr = json
        pendulum.parse(jcr["timestamp"])
        uuid.UUID(jcr["trace_id"], version=4)
        assert jcr["data"]["params"]["data"]["a"] == "b"
        assert jcr["ref"] == "a-test"
        assert jcr["project_id"] == PROJECT_NAME
        return Dummyreponse()

    monkeypatch.setattr(RaymonAPI, "login", dummylogin)
    monkeypatch.setattr(RaymonAPI, "post", test_data_post)
    apilogger = RaymonAPILogger(url="willnotbeused", project_id=PROJECT_NAME, auth_path=secret_file)
    ray = Trace(logger=apilogger)
    ray.log(ref="a-test", data=rt.Native({"a": "b"}))


def test_api_logger_tags(monkeypatch, secret_file):
    def dummylogin(self):
        pass

    def test_tags_post(self, route, json):
        assert route.startswith(f"projects/{PROJECT_NAME}/traces")
        assert route.endswith("/tags")
        jcr = json["data"]
        for tag_orig, tag_log in zip(tags, jcr):

            assert tag_orig["name"] == tag_log["name"]
            assert tag_orig["value"] == tag_log["value"]
            assert tag_orig["type"] == tag_log["type"]
            assert tag_orig["group"] == tag_log["group"]

        return Dummyreponse()

    monkeypatch.setattr(RaymonAPI, "login", dummylogin)
    monkeypatch.setattr(RaymonAPI, "post", test_tags_post)
    apilogger = RaymonAPILogger(url="willnotbeused", project_id=PROJECT_NAME, auth_path=secret_file)
    ray = Trace(logger=apilogger)
    ray.tag(tags=tags)
