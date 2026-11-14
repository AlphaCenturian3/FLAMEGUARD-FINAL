// JSDoc mirrors of contracts/schemas (contract v0.1.0). The schemas are the
// source of truth; these typedefs exist for editor checking only.

/**
 * @typedef {Object} Source
 * @property {string} title
 * @property {string} url
 * @property {string|number|null} [page]
 * @property {string|null} [quote]   Exact text from the source.
 * @property {string} retrieved      ISO date.
 * @property {string|null} [archive_id]
 */

/**
 * @typedef {"measured"|"interpretation"|"illustrative_simulation"} EvidenceClass
 */

/**
 * @typedef {Object} Investigation
 * @property {boolean} [fixture]
 * @property {string} id
 * @property {string} name
 * @property {string|null} [acronym]
 * @property {string|null} [platform]
 * @property {string[]} [objectives]
 * @property {Array<"spacecraft"|"space_station"|"lunar_base"|"martian_base"|"pressurized_rover"|"earth">} [relevant_environments]
 * @property {Source[]} sources
 */

/**
 * @typedef {Object} Finding
 * @property {boolean} [fixture]
 * @property {string} id
 * @property {string} investigation_id
 * @property {EvidenceClass} evidence_class
 * @property {string} statement
 * @property {number|string|null} [value]
 * @property {string|null} [unit]
 * @property {string|null} [uncertainty]
 * @property {Record<string, any>} provenance
 * @property {string} [label]
 */

/**
 * @typedef {Object} SimulationResult
 * @property {boolean} [fixture]
 * @property {string} id
 * @property {"illustrative_simulation"} evidence_class
 * @property {string} label
 * @property {string} model
 * @property {string} model_version
 * @property {"unverified"|"numerically_verified"|"validated_against_measured"} [verification_status]
 * @property {Record<string, any>} parameters
 * @property {Record<string, any>} outputs
 */

/**
 * Ranking item shape from master spec §5.1 (no schema file yet).
 * @typedef {Object} RankingItem
 * @property {string} investigation_id
 * @property {number} score
 * @property {string} rationale
 * @property {string[]} inputs   Finding IDs; measured or interpretation only.
 */

/**
 * Common interface implemented by the HTTP adapter and the fixture adapter.
 * @typedef {Object} DataSource
 * @property {"api"|"fixtures"} kind
 * @property {string} description
 * @property {() => Promise<{status:string, service:string, contract_version:string}>} health
 * @property {() => Promise<{items: Investigation[], contract_version?: string}>} listInvestigations
 * @property {(id: string) => Promise<Investigation>} getInvestigation
 * @property {(investigationId?: string) => Promise<{items: Finding[], contract_version?: string}>} listFindings
 * @property {(context: string) => Promise<{items: RankingItem[], contract_version?: string}>} getRankings
 * @property {(question: string) => Promise<{answer: string, citations: Source[], generated_by: string}>} ask
 * @property {(id: string) => Promise<SimulationResult>} getSimulation
 */

export {};
