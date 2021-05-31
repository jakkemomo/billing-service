"""Module with data extractor from Stripe API responses"""
import abc


class AbcPMDExtractor(abc.ABC):
    """Abstract class for payment method data extractor"""

    @staticmethod
    @abc.abstractmethod
    def extract(data: dict) -> dict:
        """
        Extract payment intent data

        @param data: data from `payment_method_details` field of PaymentIntent or Charge object
        """
        pass


class CardDataExtractor(AbcPMDExtractor):
    """Class for card data extracting"""

    @staticmethod
    def extract(data: dict) -> dict:
        """
        Extract card data

        @param data: data from `payment_method_details` field of PaymentIntent or Charge object
        @return: required data to be displayed to the client
        """
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
    """
    Factory method for getting extractor by payment method type

    @param pm_type: payment method type, e.g. `card`
    @return: extractor class instance with `AbcPMDExtractor` interface
    """
    extractor_cls = _MAPPING.get(pm_type, None)
    if not extractor_cls:
        raise ValueError()
    return extractor_cls()
