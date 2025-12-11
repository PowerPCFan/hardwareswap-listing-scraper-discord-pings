import uuid
import requests
import re as regexp
import random
import time
from typing import Any, NamedTuple, Literal
from pathlib import Path
from PIL import Image, ImageOps
from .configuration import config


def load_image_without_orientation(image_path: Path) -> Image.Image:
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    return image


class PillowImage(NamedTuple):
    object: Image.Image
    path: Path | None


def generate_combined_image_name() -> str:
    return f"combined-image-{uuid.uuid4()}.png"


def grab_direct_links(album_url: str) -> list[str] | None:
    if album_url.startswith("https://i.imgur.com/"):
        return [album_url]

    headers = {
        # microsoft edge on windows latest user agent as of early december 2025
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",  # noqa: E501
    }

    resp = requests.post(
        url="https://imgur.plen.io/api/trpc/imgur.getLinks?batch=1",
        headers=headers,
        json={
            "0": {
                "json": {
                    "url": album_url,
                },
            }
        },
    )

    data: dict = resp.json()

    # Sleep 1-3 secs before continuing since this API isn't meant to be public so it has weird rate limiting issues
    # random time just so it seems more legitimate
    time.sleep(random.uniform(1, 3))

    if not data or len(data) == 0:
        return None

    first_item: Any = data[0] if isinstance(data, list) else data

    if "error" in first_item:
        return None

    result: dict[str, Any] | None = first_item.get("result")
    if not result:
        return None

    result_data: dict[str, Any] | None = result.get("data")
    if not result_data:
        return None

    link_string: str | None = result_data.get("json")
    if not link_string:
        return None

    links: list[str] = link_string.split("\n")

    extensions = [".jpg", ".jpeg", ".png", ".gif", ".apng", ".tiff", ".tif", ".webp"]
    filtered_links = []

    for link in links:
        if not link.startswith("https://i.imgur.com/"):
            continue

        if not any(link.lower().endswith(extension) for extension in extensions):
            continue

        filtered_links.append(link)

    if not filtered_links:
        return None

    return filtered_links


def get_primary_image_from_album(album_url: str) -> str | None:
    links = grab_direct_links(album_url)

    if not links or len(links) == 0:
        return None

    return links[0]


def extract_imgur_links_from_post(post_body: str) -> list[str]:
    pattern = r"https?:\/\/(?:www\.)?imgur\.com\/(?:a|gallery)\/[A-Za-z0-9_-]+"
    matches: list[str] = regexp.findall(pattern=pattern, string=post_body)

    direct_link_pattern = r"https?:\/\/i\.imgur\.com\/[A-Za-z0-9]+\.[A-Za-z0-9]+"
    direct_links: list[str] = regexp.findall(pattern=direct_link_pattern, string=post_body)

    if not matches and not direct_links:
        return []

    if direct_links:
        matches.extend(direct_links)

    return matches


def get_primary_image_from_reddit_post(post_body: str) -> str | None:
    album_urls = extract_imgur_links_from_post(post_body)

    if not config.parse_imgur_links:
        return None

    if not album_urls or len(album_urls) == 0:
        return None

    links = grab_direct_links(album_urls[0])

    if not links or len(links) == 0:
        return None

    return links[0]


def upload_to_discord_cdn(file_path: Path, content: str = "") -> str | None:
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        with open(file_path, "rb") as f:
            files = {"file": ("image.png", f)}
            payload = {"content": content}
            response = requests.post(config.cdn_exploit_webhook, data=payload, files=files)

        if response.status_code != 200 and response.status_code != 204:
            return None

        resp_json = dict(response.json())
        attachments = resp_json.get("attachments", [])

        if not attachments:
            return None

        return attachments[0]["url"]
    except Exception:
        return None


def combine_two_images(
    input_images: list[Path] | list[Image.Image],
    image_dir: Path,
    direction: Literal["horizontal", "vertical"] = "horizontal",
    border_width: int = 12,
    scale_to_1080p: bool = True,
    write_to_disk: bool = True
) -> PillowImage | None:

    # initialize image object list
    images: list[Image.Image] = []

    for image in input_images:
        if isinstance(image, Path):
            # is an image on the disk and needs to be loaded to an image object first
            if image is None:
                continue
            loaded_image = load_image_without_orientation(image)
            images.append(loaded_image)
        elif isinstance(image, Image.Image):
            # is already an image object
            images.append(image)
        else:
            # invalid type
            continue

    if len(images) == 0:
        return None

    # +1 over the intended value because of a bug i dont feel like fixing
    max_width = 1921
    max_height = 1081

    if direction == "horizontal":
        heights = [img.height for img in images]
        target_height = min(heights)

        resized_images: list[Image.Image] = []
        total_width = border_width

        for img in images:
            aspect_ratio = img.width / img.height
            new_width = int(target_height * aspect_ratio)
            resized_img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
            resized_images.append(resized_img)
            total_width += new_width

        if scale_to_1080p and (total_width > max_width or target_height > max_height):
            width_scale = max_width / total_width if total_width > max_width else 1.0
            height_scale = max_height / target_height if target_height > max_height else 1.0
            scale_factor = min(width_scale, height_scale)

            scaled_images: list[Image.Image] = []
            total_width = int(border_width * scale_factor)
            target_height = int(target_height * scale_factor)

            for img in resized_images:
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                scaled_images.append(scaled_img)
                total_width += new_width

            resized_images = scaled_images
            border_width = int(border_width * scale_factor)

        combined_image = Image.new("RGB", (total_width, target_height), color=(0, 0, 0))
        x_offset = 0
        for i, img in enumerate(resized_images):
            combined_image.paste(img, (x_offset, 0))
            x_offset += img.width
            if i < len(resized_images) - 1:
                x_offset += border_width

    else:
        widths = [img.width for img in images]
        target_width = min(widths)

        resized_images: list[Image.Image] = []
        total_height = border_width

        for img in images:
            aspect_ratio = img.height / img.width
            new_height = int(target_width * aspect_ratio)
            resized_img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
            resized_images.append(resized_img)
            total_height += new_height

        if scale_to_1080p and (target_width > max_width or total_height > max_height):
            width_scale = max_width / target_width if target_width > max_width else 1.0
            height_scale = max_height / total_height if total_height > max_height else 1.0
            scale_factor = min(width_scale, height_scale)

            scaled_images: list[Image.Image] = []
            total_height = int(border_width * scale_factor)
            target_width = int(target_width * scale_factor)

            for img in resized_images:
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                scaled_images.append(scaled_img)
                total_height += new_height

            resized_images = scaled_images
            border_width = int(border_width * scale_factor)

        combined_image = Image.new("RGB", (target_width, total_height), color=(0, 0, 0))
        y_offset = 0
        for i, img in enumerate(resized_images):
            combined_image.paste(img, (0, y_offset))
            y_offset += img.height
            if i < len(resized_images) - 1:
                y_offset += border_width

    if not write_to_disk:
        return PillowImage(object=combined_image, path=None)
    else:
        combined_image_path = image_dir / generate_combined_image_name()
        combined_image.save(combined_image_path)
        return PillowImage(object=combined_image, path=combined_image_path)


def get_image_object_from_path(image_path: Path) -> PillowImage | None:
    if not image_path.exists():
        return None

    image = load_image_without_orientation(image_path)
    return PillowImage(object=image, path=image_path)


def create_combined_image(image_urls: list[str]) -> Path | None:
    image_dir = Path(__file__).parent.parent / "temp-images"
    image_dir.mkdir(exist_ok=True, parents=True)

    image_paths: list[Path] = []

    for image_url in image_urls:
        try:
            # uuid based off of the image url to avoid both duplicates and collisions
            ext = image_url.rsplit(".", 1)[-1] if "." in image_url else "png"
            image_name = f"{uuid.uuid5(uuid.NAMESPACE_URL, image_url)}.{ext}"
            image_path = image_dir / image_name
            image_paths.append(image_path)

            if image_path.exists():
                # already downloaded so no point in redownloading
                continue

            for _ in range(3):
                response = requests.get(image_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",  # noqa: E501
                    "Connection": "keep-alive",
                }, timeout=30)

                if response.ok:
                    break
                elif response.status_code == 429:
                    time.sleep(3)
            else:
                continue

            if len(response.content) == 0:
                continue

            with open(image_path, "wb") as f:
                f.write(response.content)

            # small delay to avoid rate limiting
            time.sleep(0.75)

        except Exception as e:
            print(f"Error downloading {image_url}: {e}")
            continue

    # these checks will probably never be hit but just in case
    if len(image_paths) == 0:
        return None

    if len(image_paths) == 1:
        return image_paths[0]

    # ok now the actual useful checks
    if len(image_paths) == 2:
        # Combine images side by side
        result = combine_two_images(image_paths, image_dir, scale_to_1080p=True, write_to_disk=True)
        return result.path if result else None

    if len(image_paths) == 3:
        # Split along the X-axis and the top gets two images side by side, bottom gets one full-width image
        last_two = combine_two_images(image_paths[1:], image_dir, scale_to_1080p=False, write_to_disk=False)

        if not last_two:
            return None

        first_image = load_image_without_orientation(image_paths[0])

        combined_image = combine_two_images(
            direction="vertical",
            input_images=[first_image, last_two.object],
            image_dir=image_dir,
            scale_to_1080p=True,
            write_to_disk=True
        )

        return combined_image.path if combined_image else None

    if len(image_paths) == 4:
        # 2x2 grid
        first_row = combine_two_images(image_paths[:2], image_dir, scale_to_1080p=False, write_to_disk=False)
        second_row = combine_two_images(image_paths[2:], image_dir, scale_to_1080p=False, write_to_disk=False)

        if not first_row or not second_row:
            return None

        combined_image = combine_two_images(
            direction="vertical",
            input_images=[first_row.object, second_row.object],
            image_dir=image_dir,
            scale_to_1080p=True,
            write_to_disk=True
        )

        return combined_image.path if combined_image else None


# ok this code got really messy but heres the main public facing function that gets called for the discord embed
def get_image_for_embed(post_body: str) -> str | None:
    if not config.parse_imgur_links:
        return None

    if not config.combine_images:
        # return first image from first album, don't combine images or upload to discord or anything
        return get_primary_image_from_reddit_post(post_body)

    imgur_album_urls = extract_imgur_links_from_post(post_body)

    imgur_image_links: list[str] = []

    for imgur_album_url in imgur_album_urls:
        images = grab_direct_links(imgur_album_url)

        if not images or len(images) == 0:
            continue

        imgur_image_links.extend(images)

    if len(imgur_image_links) == 0:
        return None
    elif len(imgur_image_links) == 1:
        # return original imgur link
        return imgur_image_links[0]
    else:
        # first, check if the list is larger than 4 and if so shrink it to avoid possible issues
        if len(imgur_image_links) > 4:
            imgur_image_links = imgur_image_links[:4]

        # combine images
        combined_image_path = create_combined_image(image_urls=imgur_image_links)

        if not combined_image_path:
            return None

        # upload to discord's cdn
        cdn_url = upload_to_discord_cdn(file_path=combined_image_path)

        if not cdn_url:
            return None

        return cdn_url
