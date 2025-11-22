from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from .models import Dataset
from .serializers import DatasetSerializer
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO

class UploadCSVView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]   # <- important for file uploads and browsable API

    def post(self, request, format=None):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response({"error": "No file uploaded"}, status=400)

        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            return Response({"error": "Invalid CSV format", "detail": str(e)}, status=400)

        required = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']
        if not all(col in df.columns for col in required):
            return Response({"error": "Missing required columns"}, status=400)

        df['Flowrate'] = pd.to_numeric(df['Flowrate'], errors='coerce')
        df['Pressure'] = pd.to_numeric(df['Pressure'], errors='coerce')
        df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')

        summary = {
            "total_count": int(len(df)),
            "averages": {
                "Flowrate": float(df['Flowrate'].mean()),
                "Pressure": float(df['Pressure'].mean()),
                "Temperature": float(df['Temperature'].mean()),
            },
            "type_distribution": df['Type'].value_counts().to_dict()
        }

        # save dataset model
        csv_file.seek(0)
        dataset = Dataset.objects.create(
            file=csv_file,
            uploaded_by=request.user,
            summary=summary,
            row_count=len(df)
        )

        # keep only last 5
        all_datasets = Dataset.objects.order_by('-uploaded_at')
        if all_datasets.count() > 5:
            for old in all_datasets[5:]:
                old.delete()

        return Response({
            "message": "Uploaded successfully",
            "summary": summary,
            "dataset_id": dataset.id
        }, status=201)


class LatestSummary(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest = Dataset.objects.order_by('-uploaded_at').first()
        if not latest:
            return Response({"error": "No dataset found"}, status=404)
        return Response(DatasetSerializer(latest).data)


class History(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        datasets = Dataset.objects.order_by('-uploaded_at')[:5]
        return Response(DatasetSerializer(datasets, many=True).data)


class GeneratePDF(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        dataset = get_object_or_404(Dataset, id=pk)
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(50, 800, f"Dataset Report - ID {pk}")
        y = 780
        for k, v in dataset.summary.items():
            p.drawString(50, y, f"{k}: {v}")
            y -= 20
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"dataset_{pk}.pdf")

