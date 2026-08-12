'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowForwardRounded } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Grid,
  Stack,
  Typography,
} from '@mui/material';
import { Job, jobsApi } from '@/lib/api';

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    jobsApi.publicList().then(setJobs);
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 7 }}>
      <Box sx={{ mb: 6 }}>
        <Typography variant="overline" color="primary">
          Open roles
        </Typography>
        <Typography variant="h1" fontWeight={850}>
          Find your next role.
        </Typography>
        <Typography color="text.secondary">
          Apply directly through the HireLens public job board.
        </Typography>
      </Box>

      <Grid container spacing={2}>
        {jobs.map((j) => (
          <Grid key={j.id} size={{ xs: 12, md: 6 }}>
            <Card sx={{ height: '100%', borderRadius: 4 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h5" fontWeight={800}>
                  {j.title}
                </Typography>
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  {j.location || 'Flexible'} · {j.employment_type || 'Full-time'}
                </Typography>
                <Typography color="text.secondary" sx={{ mt: 2 }}>
                  {j.description.slice(0, 280)}
                  {j.description.length > 280 ? '…' : ''}
                </Typography>
                <Stack
                  direction="row"
                  gap={1}
                  flexWrap="wrap"
                  sx={{ mt: 2 }}
                >
                  {j.required_skills.slice(0, 6).map((s) => (
                    <Chip key={s} size="small" label={s} />
                  ))}
                </Stack>
                <Button
                  component={Link}
                  href={`/jobs/${j.id}`}
                  endIcon={<ArrowForwardRounded />}
                  sx={{ mt: 3 }}
                >
                  View & apply
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}