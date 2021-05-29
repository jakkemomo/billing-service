import abc


class AbcPMDExtractor(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def extract(data: dict) -> dict:
        pass


class CardDataExtractor(AbcPMDExtractor):
    @staticmethod
    def extract(data: dict) -> dict:
        return {
            "brand": data["brand"],
            "exp_month": data["exp_month"],
            "exp_year": data["exp_year"],
            "last4": data["last4"],
        }


_MAPPING = {
    "card": CardDataExtractor,
}


def get_pmd_extractor(pm_type: str) -> AbcPMDExtractor:
    extractor_cls = _MAPPING.get(pm_type, None)
    if not extractor_cls:
        raise ValueError()
    return extractor_cls()
