"use client";
import { useEffect, useState } from "react";
import { Alert, Card, CardContent, Grid, Stack, Typography } from "@mui/material";
import { operationsApi } from "@/api/operations";
import type { ScreeningQueueStats } from "@/types/domain";
import { PageHeader } from "@/components/common/PageHeader";
import { PageSkeleton } from "@/components/common/LoadingState";
import { StatCard } from "@/components/common/StatCard";
import { titleCase } from "@/lib/format";
import { WorkspacesRounded } from "@mui/icons-material";

export default function OperationsPage() { const [stats,setStats]=useState<ScreeningQueueStats|null>(null); const [loading,setLoading]=useState(true); const [error,setError]=useState(""); useEffect(()=>{operationsApi.queue().then(setStats).catch(e=>setError(e instanceof Error?e.message:"Unable to load queue")).finally(()=>setLoading(false));},[]); return <Stack spacing={3}><PageHeader eyebrow="System operations" title="Screening operations" description="Monitor the asynchronous screening worker and make sure queued work is moving through the pipeline." />{loading?<PageSkeleton rows={4}/>:error?<Alert severity="error">{error}</Alert>:stats?<Grid container spacing={2}>{Object.entries(stats).map(([status,count])=><Grid key={status} size={{xs:12,sm:6,md:3}}><StatCard label={titleCase(status)} value={Number(count)} icon={<WorkspacesRounded fontSize="small"/>}/></Grid>)}</Grid>:null}<Card><CardContent><Typography fontWeight={850}>Operational model</Typography><Typography color="text.secondary" sx={{mt:1,lineHeight:1.8}}>Candidate screening is queued instead of blocking a recruiter request. Workers claim jobs, retry transient failures and persist the final screening result. This is the same separation you want before scaling beyond a single demo process.</Typography></CardContent></Card></Stack>; }
