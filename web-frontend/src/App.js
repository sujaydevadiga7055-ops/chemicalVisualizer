import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
} from "@mui/material";
import { Pie, Bar } from "react-chartjs-2";

import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
);

const API_UPLOAD = "http://127.0.0.1:8000/api/upload/";
const API_LATEST = "http://127.0.0.1:8000/api/summary/latest/";
const TOKEN = "dc7115f7e1ded18dbebf810fb9788043f38a39b5";

export default function App() {
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState(null);

  const fetchLatest = async () => {
    try {
      const res = await axios.get(API_LATEST, {
        headers: { Authorization: `Token ${TOKEN}` },
      });
      setSummary(res.data.summary || res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(API_UPLOAD, formData, {
        headers: {
          Authorization: `Token ${TOKEN}`,
          "Content-Type": "multipart/form-data",
        },
      });
      fetchLatest();
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchLatest();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" fontWeight="bold" mb={4}>
        Chemical Equipment Parameter Visualizer
      </Typography>

      {/* Upload Section */}
      <Card sx={{ mb: 4, p: 2 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>
            Upload CSV File
          </Typography>

          <Box display="flex" alignItems="center" gap={2}>
            <Button variant="contained" component="label">
              Choose File
              <input
                hidden
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
              />
            </Button>

            <Typography>{file ? file.name : "No file selected"}</Typography>

            <Button
              variant="outlined"
              onClick={handleUpload}
              disabled={!file}
            >
              Upload
            </Button>
          </Box>
        </CardContent>
      </Card>

      {summary && (
        <>
          {/* SUMMARY BOXES LIKE MOCKUP */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Card sx={{ p: 1, textAlign: "center" }}>
                <CardContent>
                  <Typography color="textSecondary">Total Count</Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {summary.total_count}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card sx={{ p: 1, textAlign: "center" }}>
                <CardContent>
                  <Typography color="textSecondary">Avg Flowrate</Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {summary.averages.Flowrate.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card sx={{ p: 1, textAlign: "center" }}>
                <CardContent>
                  <Typography color="textSecondary">Avg Pressure</Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {summary.averages.Pressure.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card sx={{ p: 1, textAlign: "center" }}>
                <CardContent>
                  <Typography color="textSecondary">
                    Avg Temperature
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {summary.averages.Temperature.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* CHARTS SECTION */}
          <Grid container spacing={3} mt={2}>
            <Grid item xs={12} md={6}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" mb={2}>
                  Equipment Type Distribution
                </Typography>

                <Pie
                  data={{
                    labels: Object.keys(summary.type_distribution),
                    datasets: [
                      {
                        data: Object.values(summary.type_distribution),
                        backgroundColor: [
                          "#4e79a7",
                          "#f28e2b",
                          "#e15759",
                          "#76b7b2",
                          "#59a14f",
                          "#edc948",
                        ],
                      },
                    ],
                  }}
                />
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" mb={2}>
                  Averages Chart
                </Typography>

                <Bar
                  data={{
                    labels: ["Flowrate", "Pressure", "Temperature"],
                    datasets: [
                      {
                        label: "Values",
                        data: [
                          summary.averages.Flowrate,
                          summary.averages.Pressure,
                          summary.averages.Temperature,
                        ],
                        backgroundColor: "#4e79a7",
                      },
                    ],
                  }}
                />
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  );
}
