from django.conf.urls import url
from hft.views import (HFTOutputView, ExportHFTCSV, ExogenousOrderUploadView,
    CustomConfigView, success_view, failed_view, HFTOrderFlowFilesListView, HFTOrderFlowListView)

urlpatterns = [
    url(HFTOutputView.url_pattern, HFTOutputView.as_view(), name=HFTOutputView.url_name),
    url(ExportHFTCSV.url_pattern, ExportHFTCSV.as_view(), name=ExportHFTCSV.url_name),
    url(CustomConfigView.url_pattern, CustomConfigView.as_view(), name=CustomConfigView.url_name),
    url(ExogenousOrderUploadView.url_pattern, ExogenousOrderUploadView.as_view(), name=ExogenousOrderUploadView.url_name),
    url('^success/$', success_view, name="success"),
    url('^failed/$', failed_view, name="failed"),
    url(HFTOrderFlowFilesListView.url_pattern, HFTOrderFlowFilesListView.as_view(), name=HFTOrderFlowFilesListView.url_name),
    url(HFTOrderFlowListView.url_pattern, HFTOrderFlowListView.as_view(), name=HFTOrderFlowListView.url_name)
]
