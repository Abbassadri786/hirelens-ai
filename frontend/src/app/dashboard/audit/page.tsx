"use client";
import { useEffect, useState } from "react";
import { Alert, Card, CardContent, Chip, Divider, Stack, Typography } from "@mui/material";
import { auditApi } from "@/api/audit";
import type { AuditEvent } from "@/types/domain";
import { PageHeader } from "@/components/common/PageHeader";
import { PageSkeleton } from "@/components/common/LoadingState";
import { formatDateTime, titleCase } from "@/lib/format";

export default function AuditPage() { const [events,setEvents]=useState<AuditEvent[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState(""); useEffect(()=>{auditApi.list().then(setEvents).catch(e=>setError(e instanceof Error?e.message:"Unable to load audit trail")).finally(()=>setLoading(false));},[]); return <Stack spacing={3}><PageHeader eyebrow="Governance" title="Audit trail" description="Trace screening operations and recruiter actions for operational accountability." />{loading?<PageSkeleton rows={6}/>:error?<Alert severity="error">{error}</Alert>:<Card><CardContent sx={{p:0}}>{events.length===0?<Typography color="text.secondary" sx={{p:4}}>No audit events recorded yet.</Typography>:<Stack divider={<Divider/>}>{events.map(event=><Stack key={event.id} direction={{xs:"column",md:"row"}} spacing={2} sx={{p:2.5}}><BoxEvent event={event}/></Stack>)}</Stack>}</CardContent></Card>}</Stack>; }
function BoxEvent({event}:{event:AuditEvent}) { return <><Stack direction="row" spacing={1} alignItems="center" sx={{minWidth:{md:230}}}><Chip size="small" label={titleCase(event.event_type)} variant="outlined"/><Typography variant="caption" color="text.secondary">{formatDateTime(event.created_at)}</Typography></Stack><Stack sx={{flex:1}}><Typography fontWeight={750}>{titleCase(event.entity_type)}</Typography><Typography variant="caption" color="text.secondary">{event.entity_id ?? "Workspace event"}</Typography></Stack><Typography variant="caption" color="text.secondary" sx={{maxWidth:480,overflow:"hidden",textOverflow:"ellipsis"}}>{Object.keys(event.metadata).length ? JSON.stringify(event.metadata) : "No additional metadata"}</Typography></>; }
