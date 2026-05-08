import express from 'express';
import cors from 'cors';
import { connect, JSONCodec } from 'nats';
import * as dotenv from 'dotenv';

dotenv.config();

const app = express();
const port = process.env.PORT || 3001;
const natsUrl = process.env.NATS_URL || 'nats://localhost:4222';

app.use(cors());

// Map of project_id -> Array of response objects (SSE connections)
const clients: Map<string, express.Response[]> = new Map();

const jc = JSONCodec();

async function startNats() {
  try {
    const nc = await connect({ servers: natsUrl });
    console.log(`Connected to NATS at ${natsUrl}`);

    // Subscribe to all telemetry datapoints
    const sub = nc.subscribe('telemetry.datapoint.v1.>');
    (async () => {
      for await (const m of sub) {
        try {
          const event: any = jc.decode(m.data);
          const projectId = event.project_id;
          
          const projectClients = clients.get(projectId);
          if (projectClients) {
            const payload = JSON.stringify(event);
            projectClients.forEach(res => {
              res.write(`data: ${payload}\n\n`);
            });
          }
        } catch (err) {
          console.error('Error processing NATS message:', err);
        }
      }
    })();
  } catch (err) {
    console.error('Failed to connect to NATS:', err);
    setTimeout(startNats, 5000);
  }
}

startNats();

app.get('/health', (_req: express.Request, res: express.Response) => res.send('OK'));

app.get('/v1/realtime/projects/:projectId', (req: express.Request, res: express.Response) => {
  const projectId = req.params.projectId as string;

  // Set headers for SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });

  // Keep connection alive
  res.write('\n');

  // Add client to the map
  if (!clients.has(projectId)) {
    clients.set(projectId, []);
  }
  clients.get(projectId)!.push(res);

  console.log(`Client connected to project ${projectId}. Total for project: ${clients.get(projectId)!.length}`);

  // Remove client on disconnect
  req.on('close', () => {
    const projectClients = clients.get(projectId);
    if (projectClients) {
      const index = projectClients.indexOf(res);
      if (index !== -1) {
        projectClients.splice(index, 1);
      }
      if (projectClients.length === 0) {
        clients.delete(projectId);
      }
    }
    console.log(`Client disconnected from project ${projectId}`);
  });
});

app.listen(port, () => {
  console.log(`Real-time service listening at http://localhost:${port}`);
});
