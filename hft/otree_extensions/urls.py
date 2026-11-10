from django.conf.urls import url
from hft.views import (
    HFTOutputView, ExportHFTCSV, ExogenousOrderUploadView,
    CustomConfigUploadView, success_view, failed_view, HFTExternalFeedFilesListView, 
    HFTOrderFlowFilesListView, HFTOrderFlowListView, ExternalFeedUploadView, 
    HFTExternalFeedListView, ping)

urlpatterns = [
    url(HFTOutputView.url_pattern, HFTOutputView.as_view(), name=HFTOutputView.url_name),
    url(ExportHFTCSV.url_pattern, ExportHFTCSV.as_view(), name=ExportHFTCSV.url_name),
    url(CustomConfigUploadView.url_pattern, CustomConfigUploadView.as_view(), name=CustomConfigUploadView.url_name),
    url(ExogenousOrderUploadView.url_pattern, ExogenousOrderUploadView.as_view(), name=ExogenousOrderUploadView.url_name),
    url(ExternalFeedUploadView.url_pattern, ExternalFeedUploadView.as_view(), name=ExternalFeedUploadView.url_name),  
    url('^success/$', success_view, name="success"),
    url('^failed/$', failed_view, name="failed"),
    url(HFTExternalFeedFilesListView.url_pattern, HFTExternalFeedFilesListView.as_view(), name=HFTExternalFeedFilesListView.url_name),
    url(HFTExternalFeedListView.url_pattern, HFTExternalFeedListView.as_view(), name=HFTExternalFeedListView.url_name),
    url(HFTOrderFlowFilesListView.url_pattern, HFTOrderFlowFilesListView.as_view(), name=HFTOrderFlowFilesListView.url_name),
    url(HFTOrderFlowListView.url_pattern, HFTOrderFlowListView.as_view(), name=HFTOrderFlowListView.url_name),
    url('^ping/$', ping, name="ping"),
]
