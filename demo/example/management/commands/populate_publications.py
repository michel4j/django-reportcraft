import datetime
from django.core.management.base import BaseCommand
from demo.example.models import Journal, Metric, Publication

JOURNAL_DATA = [
    {
        "name": "Nature",
        "metrics": {
            2018: 43.07,
            2019: 42.78,
            2020: 49.96,
            2021: 69.50,
            2022: 64.78,
            2023: 50.50,
            2024: 58.20,
        },
        "articles": [
            ("A global map of human impact on marine ecosystems", "2018-02-14"),
            ("Deep residual learning for image recognition", "2018-06-20"),
            ("Global warming of 1.5 C and anthropogenic forcing", "2018-11-05"),
            ("CRISPR-Cas9 genome editing in human stem cells", "2019-03-12"),
            ("Observation of gravitational waves from binary black holes", "2019-05-18"),
            ("Synaptic plasticity in neural network computation", "2019-08-30"),
            ("Quantum supremacy using a programmable superconducting processor", "2019-10-23"),
            ("A pneumonia outbreak associated with a new coronavirus of probable bat origin", "2020-02-03"),
            ("Structure of the SARS-CoV-2 spike glycoprotein in the prefusion conformation", "2020-02-19"),
            ("Global carbon cycle feedback uncertainties under climate warming", "2020-04-15"),
            ("High-throughput sequencing analysis of microbiome diversity", "2020-06-22"),
            ("Mapping global indigenous land stewardship and conservation", "2020-09-10"),
            ("Room-temperature superconductivity in a carbonaceous sulfur hydride", "2020-10-14"),
            ("A highly conserved neutralizing epitope on the SARS-CoV-2 spike protein", "2021-01-20"),
            ("Global trends in glacier mass loss during the twenty-first century", "2021-04-28"),
            ("Neural circuit mechanisms of visual perception", "2021-05-19"),
            ("Highly accurate protein structure prediction with AlphaFold", "2021-07-15"),
            ("The global tree restoration potential and carbon sequestration", "2021-08-11"),
            ("Superconducting circuits for quantum error correction", "2021-09-22"),
            ("Global distribution of biodiversity and conservation priorities", "2021-11-03"),
            ("Atomic-resolution structure of mammalian respiratory complex I", "2021-12-08"),
            ("Structural basis of CRISPR-Cas12a target recognition", "2022-01-19"),
            ("Global burden of bacterial antimicrobial resistance in 2019", "2022-03-09"),
            ("Climate change increases the risk of infectious disease emergence", "2022-04-28"),
            ("Mapping global urban heat islands from satellite observations", "2022-06-15"),
            ("Universal quantum computing with neutral atoms in optical tweezers", "2022-08-24"),
            ("Genome-wide association studies identify polygenic risk scores", "2022-10-12"),
            ("Evidence for a subsurface ocean on Enceladus", "2022-12-01"),
            ("Single-cell transcriptomic atlas of the human brain", "2023-03-15"),
            ("Superconductivity in infinite-layer nickelates under pressure", "2023-05-10"),
            ("Global soil carbon response to permafrost thaw", "2023-07-26"),
            ("An artificial intelligence system that masters complex strategic games", "2023-09-14"),
            ("Observation of non-Abelian anyons in quantum processors", "2023-11-20"),
            ("High-precision cosmological parameters from gravitational lensing", "2024-01-17"),
            ("Spatial transcriptomics reveals tumor microenvironment heterogeneity", "2024-02-28"),
            ("Scalable photonic quantum computing architecture", "2024-04-10"),
            ("Ocean circulation slowdown and global climate feedbacks", "2024-05-22"),
            ("Deep generative models for de novo molecular design", "2024-07-03"),
            ("Neural dynamics of memory consolidation during sleep", "2024-08-21"),
        ],
    },
    {
        "name": "Science",
        "metrics": {
            2018: 41.04,
            2019: 41.85,
            2020: 47.73,
            2021: 63.71,
            2022: 56.90,
            2023: 44.70,
            2024: 51.40,
        },
        "articles": [
            ("Cryo-EM unveils architecture of human telomerase holoenzyme", "2018-04-20"),
            ("Radar evidence of subglacial liquid water on Mars", "2018-08-03"),
            ("Ancient human DNA from Neanderthal and Denisovan lineages", "2018-12-07"),
            ("Image-guided robotic surgery for microsurgery procedures", "2019-02-15"),
            ("First M87 event horizon telescope observations", "2019-04-12"),
            ("Perovskite solar cells with certified efficiency over 25 percent", "2019-07-26"),
            ("Forest restoration at planetary scale", "2019-11-15"),
            ("Cryo-EM structure of the SARS-CoV-2 RNA polymerase", "2020-03-27"),
            ("Rapid reduction in black carbon emissions during pandemic lockdowns", "2020-05-15"),
            ("Twistronics and correlated insulator states in bilayer graphene", "2020-07-31"),
            ("Prehistoric human migration routes across North America", "2020-09-25"),
            ("Quantum advantage with photon sampling", "2020-12-18"),
            ("Structural basis of antibody neutralization of SARS-CoV-2 variants", "2021-02-19"),
            ("Global ocean warming and extreme marine heatwaves", "2021-04-09"),
            ("De novo design of protein switches for biosensing", "2021-06-18"),
            ("The origin of modern human behavioral complexity in Africa", "2021-08-27"),
            ("Deep learning enables design of functional synthetic proteins", "2021-10-15"),
            ("James Webb Space Telescope first deep field observations", "2022-07-15"),
            ("Discovery of early universe galaxies with JWST NIRCam", "2022-09-02"),
            ("Global microplastic transport across atmospheric pathways", "2022-11-18"),
            ("Room-temperature ambient pressure metallic states in hydrides", "2023-01-20"),
            ("Neural encoding of social relationships in the prefrontal cortex", "2023-04-14"),
            ("Massive methane releases from warming Arctic permafrost lakes", "2023-08-04"),
            ("CRISPR-based gene drive efficacy in mosquito populations", "2023-11-10"),
            ("Quantum simulation of chemical reaction dynamics", "2024-02-16"),
            ("Global biodiversity loss driven by land-use intensification", "2024-05-03"),
            ("Ultra-high energy cosmic rays from starburst galaxies", "2024-08-09"),
        ],
    },
    {
        "name": "Cell",
        "metrics": {
            2018: 36.22,
            2019: 38.64,
            2020: 41.58,
            2021: 66.85,
            2022: 64.50,
            2023: 45.50,
            2024: 48.90,
        },
        "articles": [
            ("Single-cell RNA sequencing reveals cell fate choices in hematopoiesis", "2018-05-03"),
            ("Metabolic rewiring in cancer cells under nutrient stress", "2018-09-20"),
            ("Epigenetic reprogramming during early mammalian development", "2019-01-24"),
            ("Immune checkpoint blockade enhances anti-tumor T cell response", "2019-06-13"),
            ("Mitochondrial dynamics regulate stem cell pluripotency", "2019-10-17"),
            ("SARS-CoV-2 entry depends on ACE2 and TMPRSS2", "2020-04-16"),
            ("A compendium of human cell types and marker genes", "2020-07-23"),
            ("Structural biology of coronavirus replication-transcription machinery", "2020-11-12"),
            ("Spatial multi-omics mapping of the mammalian heart", "2021-03-04"),
            ("Liquid-liquid phase separation in chromatin organization", "2021-06-24"),
            ("CAR-T cell persistence and efficacy in solid tumors", "2021-09-30"),
            ("Microbiome metabolites modulate neuroinflammation in Parkinson's disease", "2022-02-17"),
            ("Age-related epigenetic clocks across mammalian tissues", "2022-05-12"),
            ("Autophagy regulation of cellular senescence and longevity", "2022-09-15"),
            ("CRISPR epigenome editing restores gene expression in muscular dystrophy", "2023-02-02"),
            ("Metabolic checkpoints in dendritic cell activation", "2023-06-08"),
            ("Senolytic therapies promote tissue rejuvenation in mice", "2023-10-12"),
            ("Direct reprogramming of fibroblasts into functional cardiomyocytes", "2024-03-14"),
            ("Spatial proteomics decodes tumor immune escape pathways", "2024-07-18"),
        ],
    },
    {
        "name": "The Lancet",
        "metrics": {
            2018: 59.10,
            2019: 60.39,
            2020: 79.32,
            2021: 202.73,
            2022: 168.90,
            2023: 98.40,
            2024: 112.00,
        },
        "articles": [
            ("Global burden of cardiovascular diseases and risk factors", "2018-03-17"),
            ("Efficacy of tenofovir for pre-exposure prophylaxis of HIV-1", "2018-07-28"),
            ("Lancet Commission on pollution and health: a comprehensive review", "2018-11-10"),
            ("Food in the Anthropocene: the EAT-Lancet Commission on healthy diets", "2019-02-02"),
            ("Global prevalence of depression and anxiety in adolescents", "2019-05-18"),
            ("Dementia prevention, intervention, and care: 2020 report", "2019-09-21"),
            ("Clinical features of patients infected with 2019 novel coronavirus in Wuhan", "2020-02-15"),
            ("Remdesivir in adults with severe COVID-19: a randomized double-blind trial", "2020-05-16"),
            ("Safety and immunogenicity of the ChAdOx1 nCoV-19 vaccine", "2020-08-15"),
            ("Effectiveness of face masks and physical distancing for COVID-19 prevention", "2020-10-24"),
            ("Safety and efficacy of the BNT162b2 mRNA COVID-19 vaccine", "2021-01-09"),
            ("Long-term sequelae in patients hospitalized with COVID-19", "2021-03-27"),
            ("Global incidence and mortality of tuberculosis: 2020 surveillance", "2021-05-22"),
            ("Global excess mortality associated with COVID-19 pandemic", "2021-08-07"),
            ("Evaluating the risk of breakthrough SARS-CoV-2 infections", "2021-10-30"),
            ("Antimicrobial resistance: global burden analysis across 204 countries", "2022-02-12"),
            ("Climate change impacts on heat-related mortality across 43 countries", "2022-05-28"),
            ("Maternal and child health outcomes during global humanitarian crises", "2022-08-20"),
            ("Cardiovascular outcomes after SGLT2 inhibitor therapy in diabetes", "2022-11-12"),
            ("Mental health crisis during pandemics: global prevalence estimation", "2023-03-18"),
            ("GLP-1 receptor agonists and cardiovascular risk reduction in obesity", "2023-07-15"),
            ("Malaria vaccine R21/Matrix-M phase 3 trial efficacy and safety", "2023-11-04"),
            ("Global cancer survival trends: CONCORD-4 program findings", "2024-02-24"),
            ("Cardiovascular benefits of combination lipid-lowering therapies", "2024-06-08"),
            ("Ultra-processed foods and long-term cardiometabolic disease risk", "2024-09-21"),
        ],
    },
    {
        "name": "Journal of Machine Learning Research",
        "metrics": {
            2018: 3.82,
            2019: 4.01,
            2020: 5.18,
            2021: 6.12,
            2022: 5.80,
            2023: 6.50,
            2024: 7.20,
        },
        "articles": [
            ("Adam: A method for stochastic optimization analysis and convergence", "2018-02-10"),
            ("Understanding deep learning requires rethinking generalization", "2018-07-14"),
            ("Dropout as a Bayesian approximation: representing model uncertainty", "2019-01-18"),
            ("Attention mechanisms in transformer architectures: an empirical study", "2019-06-25"),
            ("Federated learning: strategies for privacy-preserving distributed optimization", "2019-11-08"),
            ("Exploring the limits of transfer learning with a unified text-to-text transformer", "2020-03-12"),
            ("Convex optimization algorithms with optimal convergence rates", "2020-08-20"),
            ("Implicit regularization in deep neural networks via stochastic gradient descent", "2020-12-05"),
            ("Theoretical foundations of contrastive self-supervised representations", "2021-04-15"),
            ("Diffusion probabilistic models for high-resolution generative synthesis", "2021-08-22"),
            ("Physics-informed neural networks for solving partial differential equations", "2021-11-19"),
            ("Generalization bounds for deep overparameterized neural networks", "2022-03-30"),
            ("Direct preference optimization: aligning language models without reinforcement learning", "2022-07-14"),
            ("Scaling laws for neural language models across model architectures", "2022-10-28"),
            ("Equivariant neural networks for 3D molecular conformation modeling", "2023-02-16"),
            ("Efficient fine-tuning via low-rank adaptation in large transformers", "2023-06-09"),
            ("Convergence analysis of diffusion samplers under non-log-concave priors", "2023-10-25"),
            ("Mechanistic interpretability of attention heads in multi-layer transformers", "2024-01-20"),
            ("Theoretical limits of retrieval-augmented generation and reasoning", "2024-05-18"),
            ("Scalable Bayesian optimization for high-dimensional combinatorial spaces", "2024-08-30"),
        ],
    },
    {
        "name": "Physical Review Letters",
        "metrics": {
            2018: 9.23,
            2019: 8.39,
            2020: 9.16,
            2021: 9.18,
            2022: 8.83,
            2023: 8.30,
            2024: 8.60,
        },
        "articles": [
            ("Observation of topological phases in non-Hermitian photonics", "2018-03-09"),
            ("Direct detection constraints on dark matter from LUX-ZEPLIN", "2018-08-17"),
            ("Superconductivity in twisted bilayer graphene near the magic angle", "2019-02-22"),
            ("Precision measurement of the fine-structure constant using atom interferometry", "2019-06-07"),
            ("Evidence for Majorana fermions in superconductor-semiconductor nanowires", "2019-11-29"),
            ("Experimental observation of anyonic fractional statistics in 2D electron gas", "2020-04-10"),
            ("Measurement of the muon anomalous magnetic moment at Fermilab", "2020-09-18"),
            ("Search for sub-GeV dark matter with superconducting nanowire detectors", "2021-01-15"),
            ("Quantum simulation of lattice gauge theories on neutral-atom platforms", "2021-05-28"),
            ("Observation of time crystals in periodically driven quantum spin chains", "2021-10-08"),
            ("High-field magnetic resonance of fractional quantum Hall edge states", "2022-04-01"),
            ("Precision measurement of the W-boson mass by CDF II Collaboration", "2022-07-22"),
            ("Demonstration of fault-tolerant quantum error correction on a surface code", "2022-12-09"),
            ("Experimental proof of chiral anomaly in Weyl semimetals", "2023-03-24"),
            ("Non-local quantum correlations and Bell inequality violation across kilometers", "2023-08-18"),
            ("Observation of acoustic black hole analog radiation in Bose-Einstein condensates", "2024-02-09"),
            ("Evidence of pair-density waves in iron-based high-Tc superconductors", "2024-06-14"),
        ],
    },
]


class Command(BaseCommand):
    help = "Populate dummy test data across various years for Publication, Journal, and Metric models."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing journal, metric, and publication records before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Publication.objects.all().delete()
            Metric.objects.all().delete()
            Journal.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing Journal, Metric, and Publication data."))

        journals_created = 0
        metrics_created = 0
        publications_created = 0

        for entry in JOURNAL_DATA:
            journal, _ = Journal.objects.get_or_create(name=entry["name"])
            journals_created += 1

            for year, impact_factor in entry["metrics"].items():
                _, created = Metric.objects.update_or_create(
                    journal=journal,
                    year=year,
                    defaults={"impact_factor": impact_factor},
                )
                if created:
                    metrics_created += 1

            for title, pub_date in entry["articles"]:
                published = datetime.date.fromisoformat(pub_date)
                _, created = Publication.objects.get_or_create(
                    journal=journal,
                    title=title,
                    defaults={"published": published},
                )
                if created:
                    publications_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully populated {journals_created} journals, "
                f"{metrics_created} metrics, and {publications_created} publications across years 2018-2024."
            )
        )
