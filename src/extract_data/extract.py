import re
import scrapy
from abc import ABC, abstractmethod
from .items import Item, MobileItem, PCItem


class Extract(scrapy.Spider, ABC):
    """
    Base class for all SRI spiders.
    Ensures consistent data structure and ethical defaults.
    Reads per-spider download delay from settings.py.
    """

    name = None
    source = None

    def __init__(self, *args, **kwargs):
        super(Extract, self).__init__(*args, **kwargs)
        if self.name is None:
            raise ValueError(f"{type(self).__name__} must have a name defined")
        if self.source is None:
            raise ValueError(
                f"{type(self).__name__} must have a source defined (github, xataka, etc.)"
            )

    async def start(self):
        """
        Apply per-spider download delay from settings before starting.
        """
        delays = self.settings.getdict("DOWNLOAD_DELAYS_PER_SPIDER", {})
        if self.name in delays:
            self.download_delay = delays[self.name]
        async for req in super().start():
            yield req

    @abstractmethod
    async def parse(self, response):
        """
        Standard async parse method to be implemented by children.
        """
        pass

    def create_item(
        self,
        response,
        title=None,
        content=None,
        author=None,
        date=None,
        tags=None,
        metadata=None,
    ) -> Item:
        """
        Helper method to create a Item with common fields pre-filled.
        """
        item = Item()
        item["url"] = response.url
        item["source"] = self.source
        item["title"] = title
        item["content"] = content
        item["author"] = author
        item["date"] = date
        item["tags"] = tags or []
        item["metadata"] = metadata or {}
        return item

    def create_mobile_item(
        self,
        response,
        title=None,
        content=None,
        author=None,
        date=None,
        tags=None,
        metadata=None,
        device_name=None,
        brand=None,
        os=None,
        category=None,
        article_type=None,
        specs=None,
        price=None,
        release_date=None,
    ) -> MobileItem:
        """
        Helper method to create a MobileItem with all fields pre-filled.
        Used by mobile-focused spiders.
        """
        item = MobileItem()
        item["url"] = response.url
        item["source"] = self.source
        item["title"] = title
        item["content"] = content
        item["author"] = author
        item["date"] = date
        item["tags"] = tags or []
        item["metadata"] = metadata or {}
        item["device_name"] = device_name
        item["brand"] = brand
        item["os"] = os
        item["category"] = category
        item["article_type"] = article_type
        item["specs"] = specs or {}
        item["price"] = price
        item["release_date"] = release_date
        return item

    def create_pc_item(
        self,
        response,
        title=None,
        content=None,
        author=None,
        date=None,
        tags=None,
        metadata=None,
        device_name=None,
        brand=None,
        os=None,
        category=None,
        article_type=None,
        specs=None,
        price=None,
        release_date=None,
    ) -> PCItem:
        """
        Helper method to create a PCItem with all fields pre-filled.
        Used by PC-focused spiders.
        """
        item = PCItem()
        item["url"] = response.url
        item["source"] = self.source
        item["title"] = title
        item["content"] = content
        item["author"] = author
        item["date"] = date
        item["tags"] = tags or []
        item["metadata"] = metadata or {}
        item["device_name"] = device_name
        item["brand"] = brand
        item["os"] = os
        item["category"] = category
        item["article_type"] = article_type
        item["specs"] = specs or {}
        item["price"] = price
        item["release_date"] = release_date
        return item

    def _detect_brand(self, text):
        """Detect product brand using token boundaries to avoid substring noise."""
        text = text.lower()
        brands = {
            r"\brog\s+phone\b": "ASUS",
            r"\bgalaxy\b": "Samsung",
            r"\bsamsung\b": "Samsung",
            r"\biphone\b": "Apple",
            r"\bipad\b": "Apple",
            r"\bapple\b": "Apple",
            r"\bredmi\b": "Xiaomi",
            r"\bpoco\b": "Xiaomi",
            r"\bxiaomi\b": "Xiaomi",
            r"\boneplus\b": "OnePlus",
            r"\boppo\b": "Oppo",
            r"\bvivo\b": "vivo",
            r"\bhonor\b": "Honor",
            r"\bhuawei\b": "Huawei",
            r"\bmoto\b": "Motorola",
            r"\bmotorola\b": "Motorola",
            r"\bgoogle\s+pixel\b": "Google",
            r"\bpixel\b": "Google",
            r"\bnothing\s+phone\b": "Nothing",
            r"\bnothing\b": "Nothing",
            r"\brealme\b": "Realme",
            r"\bxperia\b": "Sony",
            r"\bsony\b": "Sony",
            r"\basus\b": "ASUS",
            r"\bnokia\b": "Nokia",
            r"\bzte\b": "ZTE",
            r"\bnubia\b": "Nubia",
            r"\blenovo\b": "Lenovo",
            r"\btecno\b": "Tecno",
            r"\binfinix\b": "Infinix",
            r"\bfairphone\b": "Fairphone",
            r"\blg\b": "LG",
            r"\bdell\b": "Dell",
            r"\bhp\b": "HP",
            r"\bmsi\b": "MSI",
            r"\bacer\b": "Acer",
            r"\bintel\b": "Intel",
            r"\bamd\b": "AMD",
            r"\bnvidia\b": "NVIDIA",
        }
        for pattern, brand in brands.items():
            if re.search(pattern, text):
                return brand
        return None

    def _detect_os(self, text):
        """Detect operating system using token boundaries."""
        text = text.lower()
        os_map = {
            r"\bwindows\s+11\b": "Windows",
            r"\bwindows\s+10\b": "Windows",
            r"\bwindows\b": "Windows",
            r"\bmacos\b": "macOS",
            r"\bmac\s+os\b": "macOS",
            r"\blinux\b": "Linux",
            r"\bwatchos\b": "watchOS",
            r"\bipados\b": "iPadOS",
            r"\bipad\b": "iPadOS",
            r"\bharmonyos\b": "HarmonyOS",
            r"\bone\s+ui\b": "Android",
            r"\bmiui\b": "Android",
            r"\bhyperos\b": "Android",
            r"\bcoloros\b": "Android",
            r"\boxygenos\b": "Android",
            r"\bandroid\b": "Android",
            r"\bios\b": "iOS",
        }
        for pattern, os_name in os_map.items():
            if re.search(pattern, text):
                return os_name
        return None

  
