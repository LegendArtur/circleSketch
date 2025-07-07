import pytest
from circle_sketch.gallery.gallery import make_gallery_image
import types
import io
import os
from PIL import Image, ImageDraw

class MockUser:
    def __init__(self, display_name, avatar_path):
        self.display_name = display_name
        self.display_avatar = types.SimpleNamespace(url=avatar_path)

def create_gradient_image(path, size, direction="horizontal"):
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for i in range(size[0] if direction == "horizontal" else size[1]):
        color = (int(255 * i / (size[0] if direction == "horizontal" else size[1])), 100, 255 - int(255 * i / (size[0] if direction == "horizontal" else size[1])))
        if direction == "horizontal":
            draw.line([(i, 0), (i, size[1])], fill=color)
        else:
            draw.line([(0, i), (size[0], i)], fill=color)
    img.save(path)

def test_make_gallery_image(tmp_path):
    # Use a real image file for testing
    test_img_path = os.path.join(os.path.dirname(__file__), "test1.jpg")
    if not os.path.exists(test_img_path):
        # Create a simple test image if it doesn't exist
        from PIL import Image
        img = Image.new("RGB", (128, 128), color=(123, 222, 111))
        img.save(test_img_path)
    user = MockUser("TestUser", test_img_path)
    import requests
    real_get = requests.get
    def fake_get(url, *args, **kwargs):
        class FakeResp:
            def __init__(self, path):
                with open(path, "rb") as f:
                    self.content = f.read()
        if url == test_img_path:
            return FakeResp(test_img_path)
        return real_get(url, *args, **kwargs)
    requests.get = fake_get
    img_bytes = make_gallery_image("Test Theme", "2025-07-07", user, test_img_path)
    assert isinstance(img_bytes, io.BytesIO)
    # Optionally, save the output for manual inspection
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "gallery_result.png")
    with open(out_path, "wb") as f:
        f.write(img_bytes.getbuffer())
    assert os.path.exists(out_path) and os.stat(out_path).st_size > 0
    requests.get = real_get

@pytest.mark.parametrize("img_name,size", [
    ("test_1to1.jpg", (400, 400)),
    ("test_21to9.jpg", (420, 180)),
    ("test_9to21.jpg", (180, 420)),
])
def test_make_gallery_image_aspect(img_name, size):
    test_img_path = os.path.join(os.path.dirname(__file__), img_name)
    if not os.path.exists(test_img_path):
        create_gradient_image(test_img_path, size)
    user = MockUser("TestUser", test_img_path)
    import requests
    real_get = requests.get
    def fake_get(url, *args, **kwargs):
        class FakeResp:
            def __init__(self, path):
                with open(path, "rb") as f:
                    self.content = f.read()
        if url == test_img_path:
            return FakeResp(test_img_path)
        return real_get(url, *args, **kwargs)
    requests.get = fake_get
    img_bytes = make_gallery_image("Test Theme", "2025-07-07", user, test_img_path)
    assert isinstance(img_bytes, io.BytesIO)
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"gallery_result_{img_name}")
    with open(out_path, "wb") as f:
        f.write(img_bytes.getbuffer())
    assert os.path.exists(out_path) and os.stat(out_path).st_size > 0
    requests.get = real_get