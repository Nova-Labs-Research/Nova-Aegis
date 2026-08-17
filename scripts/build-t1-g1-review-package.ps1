[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $root 'artifacts\t1-g1-review'
$staging = Join-Path $outputRoot 'package'
$delivery = Join-Path $outputRoot 'NovaAegis-T1-G1-Independent-Review.zip'

$inputs = [ordered]@{
    'NovaAegis.ProtectedSigner-g1.zip' = @{
        Path = 'artifacts\t1-g1\NovaAegis.ProtectedSigner-g1.zip'
        Sha256 = 'CC4B6AF816F5DDFE1909F05DF4B1AA2649D4095F147028F17B2B10E7138BC126'
    }
    't1-g1-independent-artifact-review-package.md' = @{
        Path = 'docs\reviews\t1-g1-independent-artifact-review-package.md'
        Sha256 = '31F57DB5232460F468522A295672AD39073B483055D990F54B7D89D642F3F89F'
    }
    't1-g1-candidate-file-manifest.json' = @{
        Path = 'docs\evidence\t1-g1-candidate-file-manifest.json'
        Sha256 = '6E40B0AC1AA6DC1EB3BD3F579E1DC8854092E31A158A0998FA7A364BA1A9EC5C'
    }
    't1-g1-sbom.json' = @{
        Path = 'docs\evidence\t1-g1-sbom.json'
        Sha256 = '76EA6EE3BD137F081B3405384DA00A885F7394A65C3D8381CCE9BB419E60BDD7'
    }
    't1-g1-candidate-provenance.md' = @{
        Path = 'docs\evidence\t1-g1-candidate-provenance.md'
        Sha256 = 'CD3092CB08237AA1FF459CE46DFD9A90378416E67D31EAC8B6967FA9D7E546F8'
    }
    't1-gate-record.md' = @{
        Path = 'docs\transitions\t1-gate-record.md'
        Sha256 = 'AA08C37403CBFD4A5192019653C66A522EF6FF69980785A880D1DAF72AE90C80'
    }
    't1-g2-disabled-provisioning-plan.md' = @{
        Path = 'docs\transitions\t1-g2-disabled-provisioning-plan.md'
        Sha256 = 'C9E227683216279FCDCB77E79ED362B6929F46E0FD8CF75498B4BCC01B634308'
    }
}

if (Test-Path $outputRoot) {
    Remove-Item $outputRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $staging -Force | Out-Null

$checksums = foreach ($name in $inputs.Keys) {
    $source = Join-Path $root $inputs[$name].Path
    if (-not (Test-Path $source -PathType Leaf)) {
        throw "Required review input is missing: $source"
    }
    $observed = (Get-FileHash $source -Algorithm SHA256).Hash
    $expected = $inputs[$name].Sha256
    if ($null -ne $expected -and $observed -ne $expected) {
        throw "Review input hash mismatch for $name. Expected $expected, observed $observed"
    }
    Copy-Item $source (Join-Path $staging $name)
    "$observed  $name"
}

[IO.File]::WriteAllLines(
    (Join-Path $staging 'SHA256SUMS.txt'),
    [string[]]$checksums,
    [Text.UTF8Encoding]::new($false)
)
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $delivery -CompressionLevel Optimal

$deliveryHash = (Get-FileHash $delivery -Algorithm SHA256).Hash
[PSCustomObject]@{
    DeliveryPath = $delivery
    DeliverySha256 = $deliveryHash
    CandidateSha256 = $inputs['NovaAegis.ProtectedSigner-g1.zip'].Sha256
    Authority = 'NONE'
    G2 = 'BLOCKED'
    G3 = 'BLOCKED'
}