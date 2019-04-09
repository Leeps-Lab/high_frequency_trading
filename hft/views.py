import vanilla
from otree.models import Session
import hft
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import datetime
import csv
from .forms import ExogenousOrderForm, CustomConfigForm
from settings import custom_configs_directory, order_flow_configs_directory, SESSION_CONFIGS
from custom_otree_config import CustomOtreeConfig
from otree.session import SESSION_CONFIGS_DICT
from django.utils import timezone
from django.views.generic.list import ListView
from .exogenous_event import (handle_investor_file, ExogenousOrderFile,
    ExogenousOrderRecord)

class HFTOutputView(vanilla.TemplateView):
	
    url_name = 'hft_export'
    url_pattern = r'^hft_export/$'
    template_name = 'hft_extensions/Output.html'
    display_name = 'LEEPS - HFT - Download in-session trader data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = Session.objects.all().order_by('-pk')
        return context

class ExportHFTCSV(vanilla.View):

    url_name = 'hft_export_csv'
    url_pattern = r"^ExportHFTCSV/(?P<session_code>[\w.]+)/$"

    def get(self, request, *args, **kwargs):
        session_code = kwargs['session_code']
        if Session.objects.filter(code=session_code).exists():
            session = Session.objects.get(code=session_code)
            subsession_ids = [sub.id for sub in 
                hft.models.Subsession.objects.filter(session=session)]
            subsession_events = hft.output.HFTPlayerStateRecord.objects.filter(
                subsession_id__in=subsession_ids).order_by('subsession_id',
                    'market_id','timestamp')
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(
                'HFT Session {} Events (accessed {}).csv'.format(
                    session_code,
                    datetime.date.today().isoformat()))
            fieldnames = hft.output.HFTPlayerStateRecord.csv_headers
            writer = csv.DictWriter(response, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for row in subsession_events:
                writer.writerow(row.__dict__)
        return response

class UploadView:

    form_class = None
    save_directory = None
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        the_file = request.FILES['files']
        if form.is_valid():
            self.base_handle_file(the_file)           
            return HttpResponseRedirect('/success/')
        else:
            return HttpResponseRedirect('/failed/')

    def base_handle_file(self, file, *args, **kwargs):
        path = '{}/{}'.format(self.save_directory, file)
        with open(path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        self.handle_file(path)
    
    def handle_file(self, path):
        raise NotImplementedError()

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form })


class ExogenousOrderUploadView(vanilla.View, UploadView):
    template_name = 'hft_extensions/OrderFlowConfigUpload.html'
    url_name = 'order_flow_config_upload'
    url_pattern = '^order_flow_config/upload$'
    display_name = 'LEEPS - HFT - Upload Order Flow Configuration'
    form_class = ExogenousOrderForm
    save_directory = order_flow_configs_directory

    def handle_file(self, path):
        filename = path.split('/')[-1]
        with open(path, 'r') as f:
            handle_investor_file(filename, f)


class CustomConfigView(vanilla.View, UploadView):
    template_name = 'hft_extensions/CustomConfigUpload.html'
    url_name = 'custom_config'
    url_pattern = '^custom_config$'
    display_name = 'LEEPS - HFT - Upload Session Configuration'
    form_class = CustomConfigForm
    save_directory = custom_configs_directory

    def handle_file(self, path):
        new_conf = CustomOtreeConfig.from_yaml(path).get_otree_config()
        filename = new_conf['name']
        SESSION_CONFIGS_DICT[filename] = new_conf

class HFTOrderFlowFilesListView(ListView):
    url_pattern = '^order_flow_config/view_all$'
    url_name = 'order_flow_config_view_all'
    template_name = 'hft_extensions/OrderFlowConfigViewFiles.html'
    display_name = 'LEEPS - HFT - View available exogenous order flow configurations'
    model = ExogenousOrderFile

class HFTOrderFlowListView(vanilla.ListView):
    url_pattern = r'^order_flow_config/view/(?P<file_code>[\w.]+)$'
    url_name = 'order_flow_config_view'
    template_name = 'hft_extensions/OrderFlowConfigSingleFileView.html'
    model = ExogenousOrderRecord

    def get_queryset(self):
        file_record = ExogenousOrderFile.objects.get(code=self.kwargs['file_code'])
        return ExogenousOrderRecord.objects.filter(submitted_file=file_record).order_by('arrival_time')
    
def success_view(request):
    return render(request, 'hft_extensions/Success.html')

def failed_view(request):
    return render(request, 'hft_extensions/Failed.html')