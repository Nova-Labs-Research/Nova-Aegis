using System.Security.Cryptography;

namespace NovaAegis.ProtectedSigner;

internal sealed class CngSigningBoundary : IDisposable
{
    internal const string ProviderName = "Microsoft Software Key Storage Provider";
    internal const string KeyName = "NovaAegis.T1.AnchorSigner.v1";
    private readonly ECDsaCng signer;

    private CngSigningBoundary(ECDsaCng signer) => this.signer = signer;

    internal static CngSigningBoundary OpenExisting()
    {
        CngProvider provider = new(ProviderName);
        CngKey key = CngKey.Open(KeyName, provider, CngKeyOpenOptions.MachineKey);
        if (key.AlgorithmGroup != CngAlgorithmGroup.ECDsa || key.KeySize != 256)
        {
            key.Dispose();
            throw new CryptographicException("Configured T1 key algorithm is invalid.");
        }
        return new CngSigningBoundary(new ECDsaCng(key));
    }

    internal byte[] SignEnvelopeDigest(ReadOnlySpan<byte> envelopeDigest) =>
        signer.SignHash(envelopeDigest, DSASignatureFormat.IeeeP1363FixedFieldConcatenation);

    public void Dispose() => signer.Dispose();
}