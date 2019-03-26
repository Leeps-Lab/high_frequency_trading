from django.conf.urls import url
from hft.views import HFTOutputView, ExportHFTCSV

urlpatterns = [
    url(HFTOutputView.url_pattern, HFTOutputView.as_view(), name=HFTOutputView.url_name),
    url(ExportHFTCSV.url_pattern, ExportHFTCSV.as_view(), name=ExportHFTCSV.url_name)
]
