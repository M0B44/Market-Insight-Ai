USE [MarketInsight]
GO
/****** Object:  Table [dbo].[Operateurs]    Script Date: 10/21/2026 11:35:39 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Operateurs](
	[id_operateur] [int] IDENTITY(1,1) NOT NULL,
	[nom] [nvarchar](50) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id_operateur] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Catalogues]    Script Date: 10/21/2026 11:35:39 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Catalogues](
	[id_catalogue] [int] IDENTITY(1,1) NOT NULL,
	[id_operateur] [int] NOT NULL,
	[nom_fichier] [nvarchar](255) NOT NULL,
	[edition] [nvarchar](50) NULL,
	[segment] [nvarchar](10) NOT NULL,
	[url_source] [nvarchar](1000) NULL,
PRIMARY KEY CLUSTERED 
(
	[id_catalogue] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Offres]    Script Date: 10/21/2026 11:35:39 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Offres](
	[id_offre] [int] IDENTITY(1,1) NOT NULL,
	[id_catalogue] [int] NOT NULL,
	[nom_offre] [nvarchar](150) NOT NULL,
	[technologie] [nvarchar](20) NOT NULL,
	[debit_mbps] [int] NULL,
	[prix_mensuel_ttc] [decimal](10, 2) NULL,
	[engagement_mois] [int] NULL,
	[frais_installation_ttc] [decimal](10, 2) NULL,
	[appels_inclus] [nvarchar](500) NULL,
	[conditions_offre] [nvarchar](2000) NULL,
	[page_source] [int] NOT NULL,
	[extrait_source] [nvarchar](max) NOT NULL,
	[est_validee] [bit] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id_offre] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  View [dbo].[v_OffresValidees]    Script Date: 10/21/2026 11:35:39 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE VIEW [dbo].[v_OffresValidees] AS
SELECT
    o.id_offre,
    op.nom AS operateur,
    o.nom_offre,
    c.segment,
    o.technologie,
    o.debit_mbps,
    o.prix_mensuel_ttc,
    o.engagement_mois,
    o.frais_installation_ttc,
    o.appels_inclus,
    o.conditions_offre,
    c.nom_fichier,
    c.edition,
    c.url_source,
    o.page_source,
    o.extrait_source
FROM dbo.Offres AS o
INNER JOIN dbo.Catalogues AS c
    ON o.id_catalogue = c.id_catalogue
INNER JOIN dbo.Operateurs AS op
    ON c.id_operateur = op.id_operateur
WHERE o.est_validee = 1;
GO
SET IDENTITY_INSERT [dbo].[Catalogues] ON 

INSERT [dbo].[Catalogues] ([id_catalogue], [id_operateur], [nom_fichier], [edition], [segment], [url_source]) VALUES (1, 2, N'catalogue_orange.pdf', N'Juin 2023 - Fixe', N'B2C', N'https://www.orange.ma/content/download/184400/2954295/version/3/file/CATALOGUE%2BTARIFAIRE%2B%2BMobile%2BPr%C3%A9pay%C3%A9%2BMai%2B2023%2BDEF%2B%2BFixe%2BJuin%2B2023%2BDEF_compressed.pdf')
INSERT [dbo].[Catalogues] ([id_catalogue], [id_operateur], [nom_fichier], [edition], [segment], [url_source]) VALUES (2, 3, N'catalogue_inwi.pdf', NULL, N'B2C', N'https://api.inwi.ma/api/v1/ms-content/media/press/22-00095-Brochure_tarifaire_B2C-39.pdf')
INSERT [dbo].[Catalogues] ([id_catalogue], [id_operateur], [nom_fichier], [edition], [segment], [url_source]) VALUES (3, 1, N'catalogue_maroc_telecom.pdf', N'Novembre 2025', N'B2C', NULL)
SET IDENTITY_INSERT [dbo].[Catalogues] OFF
GO
SET IDENTITY_INSERT [dbo].[Offres] ON 

INSERT [dbo].[Offres] ([id_offre], [id_catalogue], [nom_offre], [technologie], [debit_mbps], [prix_mensuel_ttc], [engagement_mois], [frais_installation_ttc], [appels_inclus], [conditions_offre], [page_source], [extrait_source], [est_validee]) VALUES (1, 3, N'Fibre 200 Mbps + Premium MT TV', N'Fibre', 200, CAST(700.00 AS Decimal(10, 2)), 12, CAST(200.00 AS Decimal(10, 2)), N'Fixes nationaux illimités. 20H vers le mobile dont 4H vers l’international Zone 1.', N'Premium MT TV inclus. Frais de mise à disposition du routeur : 200 DH TTC, distincts des frais d’installation. Autres conditions : voir page 3.', 3, N'700 DH TTC /mois
Accès Fibre Optique 200 Mb/s
Accès Premium MT TV
Appels illimités vers les fixes nationaux
20H vers le mobile dont 4H vers l’international Zone 1
Engagement : 12 mois.
Frais d’installation : 200 DH TTC.', 1)
SET IDENTITY_INSERT [dbo].[Offres] OFF
GO
SET IDENTITY_INSERT [dbo].[Operateurs] ON 

INSERT [dbo].[Operateurs] ([id_operateur], [nom]) VALUES (3, N'inwi')
INSERT [dbo].[Operateurs] ([id_operateur], [nom]) VALUES (1, N'Maroc Telecom')
INSERT [dbo].[Operateurs] ([id_operateur], [nom]) VALUES (2, N'Orange')
SET IDENTITY_INSERT [dbo].[Operateurs] OFF
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [UQ__Operateu__DF90DC2C5A9C128F]    Script Date: 10/21/2026 11:35:39 AM ******/
ALTER TABLE [dbo].[Operateurs] ADD UNIQUE NONCLUSTERED 
(
	[nom] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[Offres] ADD  DEFAULT ((0)) FOR [est_validee]
GO
ALTER TABLE [dbo].[Catalogues]  WITH CHECK ADD  CONSTRAINT [FK_Catalogues_Operateurs] FOREIGN KEY([id_operateur])
REFERENCES [dbo].[Operateurs] ([id_operateur])
GO
ALTER TABLE [dbo].[Catalogues] CHECK CONSTRAINT [FK_Catalogues_Operateurs]
GO
ALTER TABLE [dbo].[Offres]  WITH CHECK ADD  CONSTRAINT [FK_Offres_Catalogues] FOREIGN KEY([id_catalogue])
REFERENCES [dbo].[Catalogues] ([id_catalogue])
GO
ALTER TABLE [dbo].[Offres] CHECK CONSTRAINT [FK_Offres_Catalogues]
GO
