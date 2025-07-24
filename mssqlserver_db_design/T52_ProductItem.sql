USE [Production]
GO

/****** Object:  Table [dbo].[T52_ProductItem]    Script Date: 2025-07-22 19:54:29 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[T52_ProductItem](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[X14] [int] NULL,
	[X15] [nvarchar](255) NULL,
	[X16] [nvarchar](255) NULL,
	[X17] [nvarchar](255) NULL,
	[X18] [int] NULL,
	[X19] [int] NULL,
	[X121] [int] NULL,
	[X122] [int] NULL,
	[X123] [int] NULL,
	[X124] [int] NULL,
	[X125] [int] NULL,
	[X126] [int] NULL,
	[X127] [int] NULL,
	[X128] [int] NULL,
	[X129] [int] NULL,
	[X20] [nvarchar](255) NULL,
	[X21] [int] NULL,
 CONSTRAINT [PK_T52_ProductItem] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

