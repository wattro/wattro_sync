from __future__ import annotations

import abc
import json
import urllib.error
import urllib.parse
import urllib.request


class RESTApi(abc.ABC):
    def _get_headers(self) -> dict:
        headers = getattr(self, "headers", None)
        if headers is None:
            raise NotImplementedError("headeres not set")
        return headers

    def _get_hostname(self) -> str:
        hostname = getattr(self, "hostname", None)
        if hostname is None:
            raise NotImplementedError("hostname not set")
        return hostname

    def _get_protocol(self) -> str:
        return getattr(self, "protocol", "https")

    def _get_base_waittime(self) -> float:
        return getattr(self, "base_waittime", 3.0)

    def _request(
            self,
            method: str,
            url: str,
            *,
            custom_header: dict | None = None,
            data: dict | None = None,
    ) -> dict:
        header = self._get_headers()
        if custom_header:
            header.update(custom_header)
        req = urllib.request.Request(url=url, method=method, headers=header, data=data)
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        return data or {}

    def _url(self, path: str, params: dict | None = None) -> str:
        param_str = ""
        if params is not None:
            param_str = "&".join(f"{key}={val}" for key, val in params.items())
        return urllib.parse.urlunparse(
            (self._get_protocol(), self._get_hostname(), path, None, param_str, None)
        )

    def _get(self, path: str, params: dict | None = None) -> dict:
        return self._request(method="GET", url=self._url(path, params))

    def _post(self, path: str, data: dict) -> dict:
        return self._request(method="POST", data=data, url=self._url(path))


class WattroNodeApi(RESTApi):
    def __init__(self, domain: str, api_key: str):
        if domain == "local":
            self.protocol = "http"
            self.hostname = "127.0.0.1:8000"
        else:
            self.protocol = "https"
            self.hostname = f"node.{domain}.wattro.de"
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        path = path.strip('/') + '/'
        return super()._get(path, params)

    def get_ref_url(self) -> str:
        return self._url("healthchecks/")

    def get_health(self) -> dict:
        return self._get("healthchecks")

    def get_assets(self, params: dict | None = None) -> dict:
        return self._get("node/asset/", params)

    def get_fields(self, path: str) -> dict:
        res = self._request(method="OPTIONS", url=self._url(path))
        return res["actions"]["POST"]

    @classmethod
    def get_healthy_api(cls, domain: str, api_key: str) -> WattroNodeApi:
        api = cls(domain, api_key)
        try:
            health = api.get_health()
        except urllib.error.URLError as urllib_err:
            raise ConnectionError(
                f"Failed to connect to {api.get_ref_url()!r}"
            ) from urllib_err

        if not health["auth_status"]["has_permission"]:
            raise ConnectionError(
                f"Not allowed to connect to {api.get_ref_url()!r}: {health}"
            )
        return api
