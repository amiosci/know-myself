import hashlib
from urllib.parse import urlparse


def hash_url(url: str) -> str:
    hasher = hashlib.new("sha256")
    hasher.update(url.encode())

    return hasher.hexdigest()


def extract_target_url(url: str):
    parsed_url = urlparse(url)

    cdn_netlocs = ["cdn.ampproject.org"]
    is_cdn = any(x in parsed_url.netloc for x in cdn_netlocs)
    if is_cdn:
        return f"{parsed_url.scheme}://{parsed_url.path[5:]}"

    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"


if __name__ == "__main__":
    url = "https://www-psychologytoday-com.cdn.ampproject.org/v/s/www.psychologytoday.com/us/blog/understanding-ptsd/202312/8-signs-of-settling-in-a-romantic-relationship?amp=&amp_gsa=1&amp_js_v=a9&usqp=mq331AQGsAEggAID#amp_tf=From%20%251%24s&aoh=17030382506853&csi=0&referrer=https%3A%2F%2Fwww.google.com&ampshare=https%3A%2F%2Fwww.psychologytoday.com%2Fus%2Fblog%2Funderstanding-ptsd%2F202312%2F8-signs-of-settling-in-a-romantic-relationship"
    hash = hash_url(url)

    expected_hash = "4216a14a6ca164691cff41ce54796bc4625f541b750b2aadfb64d69a2465d487"
    assert expected_hash == hash_url(url)

    expected_target_url = "https://www.psychologytoday.com/us/blog/understanding-ptsd/202312/8-signs-of-settling-in-a-romantic-relationship"
    assert expected_target_url == extract_target_url(url)

    non_cdn_url = "https://docs.python.org/3/library/urllib.parse.html"
    assert non_cdn_url == extract_target_url(non_cdn_url)
