import { expect, test, type Page } from '@playwright/test'
import { installTauriMock, trackPageErrors } from './helpers/tauriMock'

const conversationFixtures = [
  {
    id: 'conv-extensao',
    title: 'Ações de extensão 2026',
    contexto: '00000000-0000-0000-0000-000000000001',
    created_at: '2026-11-24T12:00:00Z',
    updated_at: '2026-11-24T12:00:00Z',
    messages: [
      {
        id: 'extensao-1', role: 'user',
        content: 'Quais são as parcerias com comunidades ribeirinhas?',
        created_at: '2026-11-24T12:00:01Z',
      },
      {
        id: 'extensao-2', role: 'assistant',
        content: 'As ações atendem comunidades do entorno do Campus Serra.',
        created_at: '2026-11-24T12:00:02Z', metadata: { type: 'chat' },
      },
    ],
  },
  {
    id: 'conv-bolsas',
    title: 'Bolsas e orientações',
    contexto: '00000000-0000-0000-0000-000000000001',
    created_at: '2026-11-23T12:00:00Z',
    updated_at: '2026-11-23T12:00:00Z',
    messages: [
      {
        id: 'bolsas-1', role: 'user', content: 'Quantas bolsas foram concedidas?',
        created_at: '2026-11-23T12:00:01Z',
      },
      {
        id: 'bolsas-2', role: 'assistant', content: 'Foram concedidas 120 bolsas no período.',
        created_at: '2026-11-23T12:00:02Z', metadata: { type: 'chat' },
      },
    ],
  },
]

const sidebar = (page: Page) => page.locator('aside[aria-label="Barra lateral"]')
const history = (page: Page) => sidebar(page).getByLabel('Histórico de conversas', { exact: true })
const conversation = (page: Page, title: string) => history(page).getByTitle(title, { exact: true })
const credits = (page: Page) => sidebar(page).getByText('Powered by LEDS & SmartIdea', { exact: true })
const aiNotice = (page: Page) => page.getByText('O Adito utiliza IA e pode cometer erros', { exact: true })

test.describe('Sidebar unificada', () => {
  test.beforeEach(async ({ page }) => {
    await installTauriMock(page, { conversations: conversationFixtures })
    await page.goto('/#/chat')
  })

  test('integra navegação e histórico, preservando a conversa ao mudar de tela', async ({ page }) => {
    const errors = trackPageErrors(page)
    await expect(sidebar(page)).toHaveCount(1)
    await expect(page.locator('aside')).toHaveCount(1)
    await expect(sidebar(page)).toHaveCSS('width', '352px')
    const settingsLink = sidebar(page).getByRole('navigation', { name: 'Navegação principal', exact: true })
      .getByRole('link', { name: 'Configurações', exact: true })
    await expect(settingsLink).toBeVisible()
    await expect(conversation(page, 'Ações de extensão 2026')).toBeVisible()
    await expect(conversation(page, 'Bolsas e orientações')).toBeVisible()

    await conversation(page, 'Bolsas e orientações').click()
    await expect(page.getByText('Foram concedidas 120 bolsas no período.', { exact: true })).toBeVisible()
    await settingsLink.click()
    await expect(page).toHaveURL(/#\/configuracoes/)
    await expect(conversation(page, 'Bolsas e orientações')).toBeVisible()
    await conversation(page, 'Ações de extensão 2026').click()
    await expect(page).toHaveURL(/#\/chat/)
    await expect(page.getByText('As ações atendem comunidades do entorno do Campus Serra.', { exact: true })).toBeVisible()
    await expect(page.getByText('Foram concedidas 120 bolsas no período.', { exact: true })).toBeHidden()

    expect(errors()).toEqual([])
  })

  test('pesquisa títulos sem acentos e conteúdo das mensagens e permite limpar a busca', async ({ page }) => {
    await sidebar(page).getByRole('button', { name: 'Pesquisar conversas', exact: true }).click()
    const search = sidebar(page).getByRole('searchbox', { name: 'Pesquisar conversas', exact: true })
    await expect(search).toBeFocused()
    await search.fill('ACOES DE EXTENSAO')
    await expect(conversation(page, 'Ações de extensão 2026')).toBeVisible()
    await expect(conversation(page, 'Bolsas e orientações')).toHaveCount(0)

    await search.fill('ribeirinhas')
    await expect(conversation(page, 'Ações de extensão 2026')).toBeVisible()
    await expect(conversation(page, 'Bolsas e orientações')).toHaveCount(0)

    await search.fill('termo inexistente')
    await expect(sidebar(page).getByText('Nenhuma conversa encontrada', { exact: false })).toBeVisible()
    await sidebar(page).getByRole('button', { name: 'Limpar pesquisa', exact: true }).click()
    await expect(search).toHaveValue('')
    await expect(conversation(page, 'Ações de extensão 2026')).toBeVisible()
    await expect(conversation(page, 'Bolsas e orientações')).toBeVisible()
  })

  test('persiste o modo recolhido e a pesquisa expande a barra e recebe foco', async ({ page }) => {
    await sidebar(page).getByRole('button', { name: 'Recolher menu', exact: true }).click()
    await expect(sidebar(page).getByRole('button', { name: 'Expandir menu', exact: true })).toBeVisible()
    await expect(history(page)).toBeHidden()
    expect(await page.evaluate(() => localStorage.getItem('adito_sidebar_collapsed'))).toBe('true')

    await page.reload()
    await expect(sidebar(page).getByRole('button', { name: 'Expandir menu', exact: true })).toBeVisible()
    await expect(credits(page)).toBeVisible()
    await expect(aiNotice(page)).toBeVisible()
    await sidebar(page).getByRole('button', { name: 'Modo Escuro', exact: true }).click()
    await expect(page.locator('html')).toHaveClass(/dark/)
    await expect(sidebar(page).getByRole('button', { name: 'Modo Claro', exact: true })).toBeVisible()
    await sidebar(page).getByRole('button', { name: 'Pesquisar conversas', exact: true }).click()
    await expect(sidebar(page).getByRole('searchbox', { name: 'Pesquisar conversas', exact: true })).toBeFocused()
    await expect(conversation(page, 'Ações de extensão 2026')).toBeVisible()
  })

  test('preserva a paleta original e o contraste ao alternar entre os temas claro e escuro', async ({ page }) => {
    const contrast = () => sidebar(page).evaluate((element) => {
      const styles = getComputedStyle(element)
      const luminance = (color: string) => {
        const [red, green, blue] = (color.match(/[\d.]+/g) || []).slice(0, 3).map(Number).map(value => {
          const channel = value / 255
          return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
        })
        return red! * 0.2126 + green! * 0.7152 + blue! * 0.0722
      }
      const background = luminance(styles.backgroundColor)
      const foreground = luminance(styles.color)
      return (Math.max(background, foreground) + 0.05) / (Math.min(background, foreground) + 0.05)
    })
    const expectOriginalPalette = async (background: string) => {
      await expect(sidebar(page)).toHaveCSS('background-color', background)
      await expect(sidebar(page).getByRole('heading', { name: 'Adito', exact: true })).toHaveCSS('color', 'rgb(255, 255, 255)')
      const navigationColor = await sidebar(page).getByRole('link', { name: 'Meu painel', exact: true }).evaluate(element =>
        (getComputedStyle(element).color.match(/[\d.]+/g) || []).map(Number),
      )
      expect(navigationColor.slice(0, 3)).toEqual([255, 255, 255])
      expect(navigationColor[3] ?? 1).toBeGreaterThanOrEqual(0.75)
      await expect(credits(page)).toBeVisible()
      await expect(aiNotice(page)).toBeVisible()
      await expect.poll(contrast).toBeGreaterThanOrEqual(4.5)
    }

    await expectOriginalPalette('rgb(23, 63, 53)')
    const darkModeButton = sidebar(page).getByRole('button', { name: 'Modo Escuro', exact: true })
    await expect(darkModeButton).toBeVisible()
    await expect(darkModeButton).toHaveText('Modo Escuro')
    await darkModeButton.click()
    await expect(page.locator('html')).toHaveClass(/dark/)
    await expectOriginalPalette('rgb(23, 27, 32)')
    const lightModeButton = sidebar(page).getByRole('button', { name: 'Modo Claro', exact: true })
    await expect(lightModeButton).toBeVisible()
    await expect(lightModeButton).toHaveText('Modo Claro')
    await lightModeButton.click()
    await expect(page.locator('html')).not.toHaveClass(/dark/)
    await expectOriginalPalette('rgb(23, 63, 53)')
  })

  test('cria conversa a partir de outra seção e mantém o histórico anterior', async ({ page }) => {
    await sidebar(page).getByRole('link', { name: 'Meu painel', exact: true }).click()
    await expect(page).toHaveURL(/#\/meu-dashboard/)
    await sidebar(page).getByRole('button', { name: 'Nova conversa', exact: true }).click()
    await expect(page).toHaveURL(/#\/chat/)
    await expect(page.getByRole('heading', { name: 'Explore a pesquisa e a extensão do Campus Serra' })).toBeVisible()
    await expect(conversation(page, 'Ações de extensão 2026')).toBeVisible()
    await expect(conversation(page, 'Bolsas e orientações')).toBeVisible()
    await expect(page.getByText('As ações atendem comunidades do entorno do Campus Serra.', { exact: true })).toBeHidden()
  })

  test('cancelar mantém a conversa; confirmar exclui a conversa ativa e abre a seguinte', async ({ page }) => {
    const title = 'Ações de extensão 2026'
    await conversation(page, title).click()
    await conversation(page, title).hover()
    await sidebar(page).getByRole('button', { name: `Excluir conversa ${title}`, exact: true }).click()
    let dialog = page.getByRole('dialog', { name: 'Excluir conversa', exact: true })
    await expect(dialog).toBeVisible()
    await dialog.getByRole('button', { name: 'Cancelar', exact: true }).click()
    await expect(conversation(page, title)).toBeVisible()

    await conversation(page, title).hover()
    await sidebar(page).getByRole('button', { name: `Excluir conversa ${title}`, exact: true }).click()
    dialog = page.getByRole('dialog', { name: 'Excluir conversa', exact: true })
    await dialog.getByRole('button', { name: 'Excluir conversa', exact: true }).click()
    await expect(dialog).toBeHidden()
    await expect(conversation(page, title)).toHaveCount(0)
    await expect(page.getByText('Foram concedidas 120 bolsas no período.', { exact: true })).toBeVisible()
    await page.reload()
    await expect(conversation(page, title)).toHaveCount(0)
  })

  test('no celular usa um único menu, fecha ao selecionar e com Escape, sem rolagem horizontal', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const menu = page.getByRole('button', { name: 'Abrir menu de navegação', exact: true })
    await menu.click()
    await expect(menu).toHaveAttribute('aria-expanded', 'true')
    await expect(conversation(page, 'Bolsas e orientações')).toBeVisible()
    await expect(credits(page)).toBeVisible()
    await conversation(page, 'Bolsas e orientações').click()
    await expect(menu).toHaveAttribute('aria-expanded', 'false')
    await expect(page.getByText('Foram concedidas 120 bolsas no período.', { exact: true })).toBeVisible()
    await expect(aiNotice(page)).toBeVisible()

    await menu.click()
    await page.keyboard.press('Escape')
    await expect(menu).toHaveAttribute('aria-expanded', 'false')
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
    await expect(page.locator('aside')).toHaveCount(1)
  })
})

test('histórico vazio permite iniciar a primeira conversa', async ({ page }) => {
  const errors = trackPageErrors(page)
  await installTauriMock(page, { conversations: [] })
  await page.goto('/#/chat')
  await expect(sidebar(page).getByRole('button', { name: 'Nova conversa', exact: true })).toBeVisible()
  await sidebar(page).getByRole('button', { name: 'Nova conversa', exact: true }).click()
  await expect(page.getByLabel('Pergunta sobre pesquisa e extensão')).toBeVisible()
  expect(errors()).toEqual([])
})
