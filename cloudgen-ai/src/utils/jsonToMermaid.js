// jsonToMermaid.js
// Converts your architecture JSON into a rich, developer-friendly Mermaid diagram.
// Supports grouping into VPC, subnets, managed services, external services, styling, and clear edges.

export default function jsonToMermaid(architecture) {
  if (!architecture || !Array.isArray(architecture.services) || architecture.services.length === 0) {
    return "graph TD\nA[No data]";
  }

  const services = architecture.services || [];
  const networking = architecture.networking || {};

  // Helpers
  const sanitizeId = (s) =>
    (s || "node")
      .toString()
      .replace(/[^A-Za-z0-9_]/g, "_")
      .replace(/^(\d)/, "_$1");

  const escapeLabel = (s) =>
    (s || "")
      .toString()
      .replace(/\[/g, "\\[")
      .replace(/\]/g, "\\]")
      .replace(/"/g, "'");

  function labelForService(svc) {
    const aws = svc.aws_service || "";
    const name = svc.name || "";
    const inst = svc.instance_type ? `(${svc.instance_type})` : "";
    const v = svc.configuration && svc.configuration.vcpus ? `${svc.configuration.vcpus} vCPU` : "";
    const m = svc.configuration && svc.configuration.memory_gb ? `${svc.configuration.memory_gb} GB` : "";
    const config = [v, m].filter(Boolean).join(" • ");
    const parts = [aws, name, inst, config].filter(Boolean);
    return escapeLabel(parts.join("<br/>"));
  }

  // Classify services
  const nodes = {};
  const appNodes = [];
  const storageNodes = [];
  const externalNodes = [];
  let albNode = null;

  services.forEach((svc) => {
    const id = sanitizeId(svc.name || svc.aws_service || "svc");
    const text = labelForService(svc);
    let cls = "compute";

    const awsLower = (svc.aws_service || "").toLowerCase();
    const nameLower = (svc.name || "").toLowerCase();

    if (/s3|amazon s3/.test(awsLower) || /s3/.test(nameLower)) {
      cls = "storage";
      storageNodes.push(id);
    } else if (/dynamodb|dynamo|rds|aurora|mysql|postgres/.test(awsLower + " " + nameLower)) {
      cls = "database";
      storageNodes.push(id);
    } else if (/stripe|paypal|external|third[-_ ]?party/.test(awsLower + " " + nameLower)) {
      cls = "external";
      externalNodes.push(id);
    } else if (/alb|load[-_ ]?balanc|elastic load balancer|elb/.test(awsLower + " " + nameLower)) {
      cls = "lb";
      albNode = id;
    } else {
      cls = "compute";
      appNodes.push(id);
    }

    nodes[id] = { svc, id, label: text, className: cls };
  });

  if (!albNode && networking && networking.load_balancer) {
    const findAlb = services.find(s =>
      /(alb|load[-_ ]?balanc|elastic load balancer|elb)/i.test((s.aws_service||'') + ' ' + (s.name||''))
    );
    if (findAlb) albNode = sanitizeId(findAlb.name || findAlb.aws_service);
  }

  const entryId = albNode || "ENTRY_ALB";
  if (!nodes[entryId]) {
    nodes[entryId] = {
      svc: { name: "load-balancer", aws_service: networking.load_balancer || "ALB" },
      id: entryId,
      label: escapeLabel((networking.load_balancer || "ALB") + "<br/>entry"),
      className: "lb",
    };
    if (!albNode) albNode = entryId;
  }

  const lines = [];
  lines.push("%%{init: {'flowchart': {'curve': 'basis'}}}%%");
  lines.push("flowchart TD");

  const vpcLabel = networking.vpc_cidr ? `VPC ${networking.vpc_cidr}` : "VPC";
  lines.push(`subgraph VPC["${vpcLabel}"]`);
  lines.push(`  subgraph PUBLIC["Public Subnets (${networking.public_subnets || 1})"]`);
  lines.push(`    ${entryId}["${nodes[entryId].label}"]`);
  lines.push("  end");

  lines.push(`  subgraph PRIVATE["Private Subnets (${networking.private_subnets || 1})"]`);
  lines.push("    subgraph APP[\"App Services\"]");
  const added = new Set();
  appNodes.forEach((id) => {
    if (!nodes[id]) return;
    lines.push(`      ${id}["${nodes[id].label}"]`);
    added.add(id);
  });
  Object.values(nodes).forEach((n) => {
    if (!added.has(n.id) && n.className === "compute" && n.id !== entryId) {
      lines.push(`      ${n.id}["${n.label}"]`);
      added.add(n.id);
    }
  });
  lines.push("    end");
  lines.push("  end");
  lines.push("end");

  if (storageNodes.length > 0) {
    lines.push(`subgraph MANAGED["Managed / Serverless Services"]`);
    storageNodes.forEach((id) => {
      if (!nodes[id]) return;
      lines.push(`  ${id}["${nodes[id].label}"]`);
    });
    lines.push("end");
  }

  if (externalNodes.length > 0) {
    lines.push(`subgraph EXTERNAL["External Services / Third Parties"]`);
    externalNodes.forEach((id) => {
      if (!nodes[id]) return;
      lines.push(`  ${id}["${nodes[id].label}"]`);
    });
    lines.push("end");
  }

  const edges = [];

  Object.values(nodes).forEach((n) => {
    if (n.className === "compute" && n.id !== entryId) {
      edges.push(`${entryId} -->|HTTPS| ${n.id}`);
    }
  });

  Object.values(nodes).forEach((n) => {
    if (n.className === "compute") {
      storageNodes.forEach((sId) => {
        edges.push(`${n.id} -->|Read/Write| ${sId}`);
      });
    }
  });

  const paymentNode = Object.values(nodes).find(n =>
    (n.svc.name || "").toLowerCase().includes("payment") ||
    (n.svc.aws_service || "").toLowerCase().includes("stripe")
  );
  if (paymentNode && externalNodes.length > 0) {
    externalNodes.forEach(extId => {
      edges.push(`${paymentNode.id} -.->|HTTPS| ${extId}`);
    });
  }

  edges.forEach(e => lines.push(e));

  lines.push("");
  lines.push("%% Styles");
  lines.push("classDef compute fill:#e6ffed,stroke:#2a7a2a,stroke-width:1px;");
  lines.push("classDef storage fill:#e8f4ff,stroke:#0b5394,stroke-width:1px;");
  lines.push("classDef database fill:#eef7ff,stroke:#0b5394,stroke-width:2px,stroke-dasharray: 4 2;");
  lines.push("classDef external fill:#f5f5f5,stroke:#666,stroke-width:1px,stroke-dasharray: 2 2;");
  lines.push("classDef lb fill:#fff3cc,stroke:#b07b00,stroke-width:1px;");

  Object.values(nodes).forEach(n => {
    let cls = n.className;
    if (cls === "storage") cls = "storage";
    if (cls === "database") cls = "database";
    if (cls === "external") cls = "external";
    if (cls === "lb") cls = "lb";
    if (cls === "compute") cls = "compute";
    lines.push(`class ${n.id} ${cls};`);
  });

  lines.push("");
  lines.push("subgraph LEGEND[\"Legend\"]");
  lines.push("  L1[(LB)]");
  lines.push("  C1[(Compute)]");
  lines.push("  S1[(Storage/DB)]");
  lines.push("  X1[(External)]");
  lines.push("end");
  lines.push("class L1 lb; class C1 compute; class S1 storage; class X1 external;");

  return lines.join("\n");
}

// /**
//  * jsonToMermaid.js
//  *
//  * Converts a detailed architecture JSON into a highly accurate and visually rich Mermaid diagram.
//  * This version is designed for extensibility and accuracy, capable of handling a wide range of AWS services.
//  *
//  * Key Features:
//  * - Extensible Service Map: Easily add new AWS services by defining their category and icon.
//  * - Font Awesome Icons: Provides clear visual cues for each service type.
//  * - Intelligent Edge Generation: Prioritizes a `connections` array from the source JSON for diagram accuracy.
//  * - Smart Fallbacks: Provides sensible default connections if the `connections` array is not present.
//  * - Clean Code Structure: Separates data classification from markup generation for maintainability.
//  */

// // --- The Service Dictionary ---
// // This is the heart of the system. Add any AWS service here to support it.
// // Categories: lb, compute, storage, database, network, security, analytics, ml, external
// const SERVICE_MAP = {
//   // Load Balancers
//   "alb": { category: "lb", icon: "fa:fa-network-wired" },
//   "elb": { category: "lb", icon: "fa:fa-network-wired" },
//   "load balancer": { category: "lb", icon: "fa:fa-network-wired" },
//   // Compute
//   "ec2": { category: "compute", icon: "fa:fa-server" },
//   "lambda": { category: "compute", icon: "fa:fa-bolt" },
//   "ecs": { category: "compute", icon: "fa:fa-cubes" },
//   "eks": { category: "compute", icon: "fa:fa-dharmachakra" },
//   "fargate": { category: "compute", icon: "fa:fa-shipping-fast" },
//   "beanstalk": { category: "compute", icon: "fa:fa-seedling" },
//   // Storage
//   "s3": { category: "storage", icon: "fa:fa-archive" },
//   "efs": { category: "storage", icon: "fa:fa-file-alt" },
//   "fsx": { category: "storage", icon: "fa:fa-hdd" },
//   "glacier": { category: "storage", icon: "fa:fa-snowflake" },
//   // Databases
//   "rds": { category: "database", icon: "fa:fa-database" },
//   "aurora": { category: "database", icon: "fa:fa-database" },
//   "dynamodb": { category: "database", icon: "fa:fa-table" },
//   "documentdb": { category: "database", icon: "fa:fa-file-invoice" },
//   "mysql": { category: "database", icon: "fa:fa-database" },
//   "postgres": { category: "database", icon: "fa:fa-database" },
//   "redis": { category: "caching", icon: "fa:fa-memory" },
//   "elasticache": { category: "caching", icon: "fa:fa-memory" },
//   // Networking & Content Delivery
//   "vpc": { category: "network", icon: "fa:fa-sitemap" },
//   "route 53": { category: "network", icon: "fa:fa-route" },
//   "cloudfront": { category: "network", icon: "fa:fa-cloud" },
//   "api gateway": { category: "network", icon: "fa:fa-door-open" },
//   "internet gateway": { category: "network", icon: "fa:fa-globe" },
//   "nat gateway": { category: "network", icon: "fa:fa-random" },
//   // Security
//   "iam": { category: "security", icon: "fa:fa-user-shield" },
//   "kms": { category: "security", icon: "fa:fa-key" },
//   "waf": { category: "security", icon: "fa:fa-shield-alt" },
//   // Analytics & Messaging
//   "kinesis": { category: "analytics", icon: "fa:fa-stream" },
//   "sqs": { category: "messaging", icon: "fa:fa-envelope-open-text" },
//   "sns": { category: "messaging", icon: "fa:fa-bullhorn" },
//   "eventbridge": { category: "messaging", icon: "fa:fa-calendar-alt" },
//   // External Services
//   "user": { category: "external", icon: "fa:fa-user" },
//   "external": { category: "external", icon: "fa:fa-external-link-alt" },
//   "third-party": { category: "external", icon: "fa:fa-external-link-alt" },
// };

// // --- Helper Functions ---
// const sanitizeId = (s) => (s || "node").toString().replace(/[^A-Za-z0-9_]/g, "_");
// const escapeLabel = (s) => (s || "").toString().replace(/"/g, "'");

// /**
//  * Processes the raw architecture JSON and classifies all services.
//  * @param {object} architecture - The architecture JSON from the backend.
//  * @returns {object} - A structured object containing nodes and connections.
//  */
// function classifyServices(architecture) {
//   const services = architecture.services || [];
//   const nodes = new Map();

//   services.forEach((svc) => {
//     const id = sanitizeId(svc.name || svc.aws_service);
//     if (!id) return;

//     const combinedText = `${svc.aws_service || ""} ${svc.name || ""}`.toLowerCase();
//     let nodeInfo = { category: "compute", icon: "fa:fa-server" }; // Default

//     for (const keyword in SERVICE_MAP) {
//       if (combinedText.includes(keyword)) {
//         nodeInfo = SERVICE_MAP[keyword];
//         break;
//       }
//     }

//     nodes.set(id, {
//       id,
//       label: `"${escapeLabel(nodeInfo.icon)} ${escapeLabel(svc.name || svc.aws_service)}<br/><small>${escapeLabel(svc.instance_type || svc.aws_service)}</small>"`,
//       category: nodeInfo.category,
//     });
//   });

//   return {
//     nodes,
//     connections: architecture.connections || [],
//     networking: architecture.networking || {},
//   };
// }

// /**
//  * Generates the Mermaid diagram string from classified service data.
//  * @param {object} processedData - The output from classifyServices.
//  * @returns {string} - The complete Mermaid diagram string.
//  */
// function generateMermaidMarkup({ nodes, connections }) {
//   const lines = ["flowchart TD"];
//   lines.push(`%% --- Nodes Definition ---`);

//   // Group nodes by category for subgraph generation
//   const nodesByCategory = Array.from(nodes.values()).reduce((acc, node) => {
//     acc[node.category] = [...(acc[node.category] || []), node];
//     return acc;
//   }, {});

//   // Define User/External nodes outside VPC
//   (nodesByCategory.external || []).forEach(node => lines.push(`${node.id}${node.label}`));

//   // Define VPC and its subgraphs
//   lines.push(`subgraph VPC`);
//   (nodesByCategory.network || []).forEach(node => lines.push(`  ${node.id}${node.label}`));
//   (nodesByCategory.lb || []).forEach(node => lines.push(`  ${node.id}${node.label}`));
//   (nodesByCategory.compute || []).forEach(node => lines.push(`  ${node.id}${node.label}`));
//   lines.push(`end`);

//   // Define AWS Managed Services outside VPC
//   const managedCategories = ["database", "storage", "caching", "analytics", "messaging", "security"];
//   const managedNodes = managedCategories.flatMap(cat => nodesByCategory[cat] || []);
//   if (managedNodes.length > 0) {
//     lines.push(`subgraph AWS Managed Services`);
//     managedNodes.forEach(node => lines.push(`  ${node.id}${node.label}`));
//     lines.push(`end`);
//   }

//   lines.push(`\n%% --- Edges (Connections) ---`);
//   if (connections && connections.length > 0) {
//     // --- Intelligent Edge Generation ---
//     connections.forEach(conn => {
//       const from = sanitizeId(conn.from);
//       const to = sanitizeId(conn.to);
//       const label = conn.label ? `|${escapeLabel(conn.label)}|` : "";
//       if (nodes.has(from) && nodes.has(to)) {
//         lines.push(`${from} -->${label} ${to}`);
//       }
//     });
//   } else {
//     // --- Smart Fallback Edge Generation ---
//     const entryPoints = nodesByCategory.external || nodesByCategory.lb || [];
//     const computePoints = nodesByCategory.compute || [];
//     const dataPoints = [...(nodesByCategory.database || []), ...(nodesByCategory.storage || [])];

//     entryPoints.forEach(entry => {
//       (nodesByCategory.lb || computePoints).forEach(target => lines.push(`${entry.id} --> ${target.id}`));
//     });
//     computePoints.forEach(compute => {
//       dataPoints.forEach(data => lines.push(`${compute.id} --> ${data.id}`));
//     });
//   }

//   // --- Styling ---
//   lines.push(
//     `\n%% --- Class Definitions for Styling ---`,
//     `classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;`,
//     `classDef external fill:#f0f0f0,stroke:#555,stroke-width:2px,stroke-dasharray: 3 3;`,
//     `classDef compute fill:#e6ffed,stroke:#2a7a2a,stroke-width:2px;`,
//     `classDef storage fill:#e8f4ff,stroke:#0b5394,stroke-width:2px;`,
//     `classDef database fill:#fff0e6,stroke:#d9534f,stroke-width:2px;`,
//     `classDef caching fill:#fff9e6,stroke:#f0ad4e,stroke-width:2px;`,
//     `classDef messaging fill:#fde8ff,stroke:#9b59b6,stroke-width:2px;`,
//     `classDef lb fill:#e6f7ff,stroke:#31708f,stroke-width:2px;`,
//     `classDef network fill:#f4f4f4,stroke:#aaa,stroke-width:1px,stroke-dasharray: 5 5;`,
//     `classDef security fill:#ffe6e6,stroke:#a94442,stroke-width:2px;`
//   );
//   nodes.forEach(node => lines.push(`class ${node.id} ${node.category};`));

//   return lines.join("\n");
// }

// /**
//  * Main function to convert architecture JSON to a Mermaid diagram string.
//  * @param {object} architecture - The architecture JSON object.
//  * @returns {string} - A string representing the Mermaid diagram.
//  */
// export default function jsonToMermaid(architecture) {
//   if (!architecture || !Array.isArray(architecture.services) || architecture.services.length === 0) {
//     return "graph TD\n  A[No architecture data provided];";
//   }

//   const processedData = classifyServices(architecture);
//   return generateMermaidMarkup(processedData);
// }