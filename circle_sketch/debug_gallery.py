# Debug script for gallery image generation
from PIL import Image
from .gallery.gallery import make_gallery_image
import types
import os

class MockUser:
    def __init__(self, display_name, avatar_path):
        self.display_name = display_name
        self.display_avatar = types.SimpleNamespace(url=avatar_path)

def run_test(test_img, out_img, user_name="TestUser"):
    theme = "A Dragon's Hoard"
    date_str = "July 7, 2025"
    user = MockUser(user_name, test_img)
    import requests
    real_get = requests.get
    def fake_get(url, *args, **kwargs):
        class FakeResp:
            def __init__(self, path):
                with open(path, "rb") as f:
                    self.content = f.read()
        if url == test_img:
            return FakeResp(test_img)
        return real_get(url, *args, **kwargs)
    requests.get = fake_get
    img_bytes = make_gallery_image(theme, date_str, user, test_img)
    with open(out_img, "wb") as f:
        f.write(img_bytes.getbuffer())
    print(f"Saved {out_img}")
    requests.get = real_get

if __name__ == "__main__":
    for i in range(1, 4):
        test_img = f"test{i}.jpg"
        out_img = f"temp_result{i}.jpg"
        if os.path.exists(test_img):
            run_test(test_img, out_img, user_name=f"TestUser{i}")
        else:
            print(f"{test_img} not found, skipping.")
