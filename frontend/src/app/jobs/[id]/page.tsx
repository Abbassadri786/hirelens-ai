'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowBackRounded,
  CheckCircleOutlineRounded,
} from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { Job, jobsApi } from '@/lib/api';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function cookie(n: string) {
  return (
    document.cookie
      .split('; ')
      .find((x) => x.startsWith(`${n}=`))
      ?.split('=')[1] ?? null
  );
}

export default function Apply() {
  const p = useParams<{ id: string }>();
  const [j, setJ] = useState<Job | null>(null);
  const [e, setE] = useState('');
  const [ok, setOk] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [f, setF] = useState({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    cover_letter: '',
  });

  useEffect(() => {
    jobsApi
      .getPublic(p.id)
      .then(setJ)
      .catch((x) => setE(x instanceof Error ? x.message : 'Job not found'));
  }, [p.id]);

  const submit = async (ev: FormEvent) => {
    ev.preventDefault();
    setE('');
    if (!file) {
      setE('Attach a PDF or DOCX resume.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setE('Resume must be 10 MB or smaller.');
      return;
    }
    await fetch(`${API}/api/v1/auth/csrf`, { credentials: 'include' });
    const csrf = cookie('hirelens_csrf');
    if (!csrf) {
      setE('Security token could not be initialized. Refresh and retry.');
      return;
    }
    const data = new FormData();
    Object.entries(f).forEach(([k, v]) => data.append(k, v));
    data.append('resume_file', file);
    const r = await fetch(`${API}/api/v1/applications/public/jobs/${p.id}`, {
      method: 'POST',
      body: data,
      credentials: 'include',
      headers: { 'X-CSRF-Token': decodeURIComponent(csrf) },
    });
    if (!r.ok) {
      const b = await r.json().catch(() => ({}));
      setE(b.detail ?? 'Application failed');
      return;
    }
    setOk(true);
  };

  if (ok)
    return (
      <Container maxWidth="sm" sx={{ py: 12 }}>
        <Card>
          <CardContent sx={{ p: 5, textAlign: 'center' }}>
            <CheckCircleOutlineRounded color="success" sx={{ fontSize: 64 }} />
            <Typography variant="h4" fontWeight={850}>
              Application submitted
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Your resume was received and parsed. AI screening arrives in Phase
              3.
            </Typography>
            <Button component={Link} href="/jobs" sx={{ mt: 3 }}>
              Browse roles
            </Button>
          </CardContent>
        </Card>
      </Container>
    );

  if (!j)
    return (
      <Container sx={{ py: 10 }}>
        <Alert severity={e ? 'error' : 'info'}>{e || 'Loading job…'}</Alert>
      </Container>
    );

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Button component={Link} href="/jobs" startIcon={<ArrowBackRounded />}>
        All jobs
      </Button>

      <Box
        sx={{
          mt: 5,
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '1fr 420px' },
          gap: 3,
        }}
      >
        <Card>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="overline" color="primary">
              Open role
            </Typography>
            <Typography variant="h2" fontWeight={850}>
              {j.title}
            </Typography>
            <Typography color="text.secondary">
              {j.location || 'Flexible'} · {j.employment_type || 'Full-time'}
            </Typography>
            <Typography
              sx={{ mt: 4, whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
            >
              {j.description}
            </Typography>
            <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 4 }}>
              {j.required_skills.map((s) => (
                <Chip key={s} label={s} color="primary" variant="outlined" />
              ))}
            </Stack>
          </CardContent>
        </Card>

        <Card component="form" onSubmit={submit}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h5" fontWeight={800}>
              Apply for this role
            </Typography>

            <Stack spacing={2} sx={{ mt: 3 }}>
              {e && <Alert severity="error">{e}</Alert>}
              <TextField
                label="Full name"
                required
                value={f.full_name}
                onChange={(x) => setF({ ...f, full_name: x.target.value })}
              />
              <TextField
                label="Email"
                type="email"
                required
                value={f.email}
                onChange={(x) => setF({ ...f, email: x.target.value })}
              />
              <TextField
                label="Phone"
                value={f.phone}
                onChange={(x) => setF({ ...f, phone: x.target.value })}
              />
              <TextField
                label="Location"
                value={f.location}
                onChange={(x) => setF({ ...f, location: x.target.value })}
              />
              <TextField
                label="Cover letter"
                multiline
                minRows={4}
                value={f.cover_letter}
                onChange={(x) => setF({ ...f, cover_letter: x.target.value })}
              />
              <Button component="label" variant="outlined">
                {file ? file.name : 'Choose resume'}
                <input
                  hidden
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(x) => setFile(x.target.files?.[0] ?? null)}
                />
              </Button>
              <Button type="submit" variant="contained" size="large">
                Submit application
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
}