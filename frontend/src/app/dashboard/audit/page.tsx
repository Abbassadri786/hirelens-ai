"use client";

import { useEffect, useState } from "react";
import { Alert, Card, CardContent, Container, Divider, Stack, Typography } from "@mui/material";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { auditApi, AuditEvent } from "@/lib/api-phase5-8";

function Content() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    auditApi.list()
      .then(setEvents)
      .catch(e => setError(e instanceof Error ? e.message : "Unable to load audit events"));
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 5 }}>
      <Typography variant="overline" color="primary" fontWeight={800}>Compliance</Typography>
      <Typography variant="h2" fontWeight={850}>Audit trail</Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Screening actions are recorded for traceability. Do not use these logs as an automated hiring decision.
      </Typography>
      {error && <Alert severity="error">{error}</Alert>}
      <Card sx={{ borderRadius: 4, mt: 3 }}>
        <CardContent>
          <Stack divider={<Divider />} spacing={2}>
            {events.map(event => (
              <div key={event.id}>
                <Typography fontWeight={800}>{event.event_type}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {event.entity_type} · {new Date(event.created_at).toLocaleString()}
                </Typography>
                {Object.keys(event.metadata).length > 0 && (
                  <Typography variant="caption">
                    {JSON.stringify(event.metadata)}
                  </Typography>
                )}
              </div>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </Container>
  );
}

export default function Page() {
  return <ProtectedRoute><Content /></ProtectedRoute>;
}
