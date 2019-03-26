import vanilla
from otree.models import Session
import hft
from django.http import HttpResponse
import datetime
import csv

class HFTOutputView(vanilla.TemplateView):
	
    url_name = 'hft_export'
    url_pattern = r'^hft_export/$'
    template_name = 'hft_extensions/Output.html'
    display_name = 'HFT Data Export'

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